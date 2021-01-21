from qunetsim.backends.rw_lock import RWLock
from qunetsim.backends.safe_dict import SafeDict
from qunetsim.objects.qubit import Qubit
from qunetsim.objects import Logger
from qunetsim.objects.packets.packet import Packet
from qunetsim.utils.constants import Constants
from qunetsim.utils.serialization import Serialization
from qunetsim.utils.serialization.network_objects import SingleGate, DoubleGate,\
                                Measure, NewQubit, CreateEntangledPair, MeasurementResult
from queue import Queue
import uuid
from copy import deepcopy as dp
import enum
import time
try:
    import serial
    import serial.threaded
except ImportError:
    raise RuntimeError("To use the Emulated Backend you need to install "
                       "pyserial!")


####################################
# Networking card definitions
####################################
QUANTUM_NETWORKCARD_TIMEOUT = 10

####################################
#   Payload Definitions and Types
####################################
signal_payload = [["sender", None, Serialization.SIZE_HOST_ID * 8],
                     ["sequence_number", None, Serialization.SIZE_SEQUENCE_NR * 8],
                     ["message", None, Serialization.SIZE_MSG_CONTENT * 8]]
classical_payload = [["sender", None, Serialization.SIZE_HOST_ID * 8],
                     ["sequence_number", None, Serialization.SIZE_SEQUENCE_NR * 8],
                     ["message", None, Serialization.SIZE_MSG_CONTENT * 8]]
quantum_payload = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                   ["qunetsim_qubit_id", None, Serialization.SIZE_QUNETSIM_QUBIT_ID * 8]]

payload_type_to_payload = [signal_payload, classical_payload, quantum_payload]

calculate_bit_length = lambda x: sum([a[2] for a in x])

####################################
#    Frame Definitions
####################################
idle_frame = {}
single_gate_frame = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, Serialization.SIZE_GATE_PARAMETER * 8]]
double_gate_frame = [["first_qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                     ["second_qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, Serialization.SIZE_GATE_PARAMETER * 8]]
measure_frame = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                 ["non_destructive", None, 1],
                 ["reserved", 0, 7]]
measurement_result_frame = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                            ["measurement_result", None, 1],
                            ["non_destructive", None, 1],
                            ["reserved", 0, 6]]
new_qubit_frame = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8]]
send_qubit_frame = [["qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                    ["host_to_send_to", None, 64]]
create_epr_frame = [["first_qubit_id", None, Serialization.SIZE_QUBIT_ID * 8],
                    ["second_qubit_id", None, Serialization.SIZE_QUBIT_ID * 8]]
network_packet_frame = [["sender", None, Serialization.SIZE_HOST_ID * 8],
                  ["receiver", None, Serialization.SIZE_HOST_ID * 8],
                  ["sequence_number", None, Serialization.SIZE_SEQUENCE_NR * 8],
                  ["protocol", None, Serialization.SIZE_PROTOCOL * 8],
                  ["payload_type", None, Serialization.SIZE_PAYLOAD_TYPE * 8],
                  ["await_ack", None, 1],
                  ["reserved", 0, 7],
                  ["payload", None, max([calculate_bit_length(x) for x in payload_type_to_payload])]]

Command_to_frame = [idle_frame, single_gate_frame, double_gate_frame,
                    measure_frame, new_qubit_frame, send_qubit_frame,
                    create_epr_frame, network_packet_frame]

Network_command_to_frame = [idle_frame, measurement_result_frame, network_packet_frame]

command_basis_frame = [['command', None, 8]]


def network_command_to_amount_of_bytes(command):
    # returns the size of the data frame from the command
    command = Serialization.binary_to_integer(command)
    Logger.get_instance().log("received command "+ str(command))
    return command, int(calculate_bit_length(Network_command_to_frame[command])/8)


def command_to_amount_of_bytes(command):
    # returns the size of the data frame from the command
    command = Serialization.binary_to_integer(command)
    return command, int(calculate_bit_length(Command_to_frame[command])/8)


def binary_to_object(command, binary_string):
    if command == Serialization.NetworkCommands.IDLE:
        return None
    elif command == Serialization.NetworkCommands.MEASUREMENT_RESULT:
        return MeasurementResult.from_binary(binary_string)
    elif command == Serialization.NetworkCommands.RECV_NETWORK_PACKET:
        return Packet.from_binary(binary_string)
    else:
        raise ValueError("Received command from Networking card is not valid.")


class EmulationBackend(object):
    """
    Backend which connects to a Quantum Networking Card.
    """

    class NetworkingCard(serial.threaded.Protocol):
        # There only should be one instance of NetworkingCard
        __instance = None

        IDLE_STATE = 0
        WAIT_FOR_DATA = 1

        @staticmethod
        def get_instance():
            if EmulationBackend.NetworkingCard.__instance is not None:
                return EmulationBackend.NetworkingCard.__instance
            else:
                return EmulationBackend.NetworkingCard()

        def __init__(self):
            if EmulationBackend.NetworkingCard.__instance is not None:
                raise Exception("Call get instance to get the object.")
            EmulationBackend.NetworkingCard.__instance = self
            ser = serial.Serial('/dev/ttyUSB1', 115200)
            self._listener_dict = SafeDict()
            self._virtual_network = None  # virtual network which distributes messages to the right hosts
            self._notifier_list = []
            self._receiver_lock = RWLock()  # to make sure that data is not read in parallel
            self._sender_lock = RWLock()
            self._command_of_frame = 0  # description of the frame to be filled
            self._bytes_read_of_frame = 0  # bytes received of the current frame
            self._total_bytes_of_frame = 0  # total bytes in the frame currently receiving
            self._current_frame_bytes = None  # buffer for the bytes of the current frame
            self._receiver_state = EmulationBackend.NetworkingCard.IDLE_STATE
            self._reader = serial.threaded.ReaderThread(ser, self)
            self._reader.start()

        def __del__(self):
            self._reader.__exit__()

        def __call__(self):
            return self

        def add_notify_on_recv(self, return_queue, command, identification):
            """
            Add a function which should be called if certain data arrives.
            The data to be arrived is specified by command of the received
            frame from the networking card as well as host_id/qubit_id/etc.

            Args:
                return_queue (Queue): Queue to which the result is send.
                command (Serialization.NetworkCommands): Command for which is waited.
                identification (int): Identification, depends on the command.
            """
            notification = [return_queue, command, identification]
            self._notifier_list.append(notification)

        def _process_frame_data(self, data):
            if self._total_bytes_of_frame > (self._bytes_read_of_frame + len(data)):
                self._bytes_read_of_frame += len(data)
                self._current_frame_bytes += data
                return len(data)
            else:
                append_length = self._total_bytes_of_frame - self._bytes_read_of_frame
                data_append = data[:append_length]
                self._bytes_read_of_frame += append_length
                self._current_frame_bytes += data_append
                return append_length

        def _handle_finished_frame(self):
            object = binary_to_object(self._command_of_frame, self._current_frame_bytes)
            if self._command_of_frame == Serialization.NetworkCommands.RECV_NETWORK_PACKET:
                # send the packet to the virtual network
                self._virtual_network.send(object)
            elif self._command_of_frame == Serialization.NetworkCommands.MEASUREMENT_RESULT:
                Logger.get_instance().log("Measurement result " + str(self._notifier_list))
                # send the measurement result to the right person
                for notify in self._notifier_list:
                    Logger.get_instance().log("here 1")
                    # check if command and qubit id both match
                    if notify[1] == Serialization.NetworkCommands.MEASUREMENT_RESULT:
                        Logger.get_instance().log("here 2")
                        Logger.get_instance().log(str(notify[2]) + " == " + str(object.id))
                        if notify[2] == object.id.bytes:
                            Logger.get_instance().log("here 3")
                            notify[0].put(object)
                            # remove element from the notifier list
                            self._notifier_list.remove(notify)
            else:
                Logger.get_instance().error("Received undefined frame!")

        def send_bytestring(self, byte_string):
            Logger.get_instance().log("Send byte string " + str(byte_string))
            self._sender_lock.acquire_write()
            self._reader.write(byte_string)
            time.sleep(0.1)
            self._sender_lock.release_write()

        def data_received(self, data, lock_active=False):
            if not lock_active:
                self._receiver_lock.acquire_write()

            if self._receiver_state == EmulationBackend.NetworkingCard.IDLE_STATE:
                self._receiver_state = EmulationBackend.NetworkingCard.WAIT_FOR_DATA
                self._command_of_frame, self._total_bytes_of_frame = network_command_to_amount_of_bytes(data[0:1])
                Logger.get_instance().log(str(self._total_bytes_of_frame) + " bytes expected")
                self._current_frame_bytes = b''
                self._bytes_read_of_frame = 0
                if len(data) > 1:
                    data = data[1:]  # remove command from the data
                else:
                    self._receiver_lock.release_write()
                    return

            if self._receiver_state == EmulationBackend.NetworkingCard.WAIT_FOR_DATA:
                amount_read = self._process_frame_data(data)
                if self._bytes_read_of_frame == self._total_bytes_of_frame:
                    self._handle_finished_frame()
                    self._receiver_state = EmulationBackend.NetworkingCard.IDLE_STATE
                    self._bytes_read_of_frame = 0
                    self._current_frame_bytes = None

                if amount_read < len(data):
                    self.data_received(data[amount_read:], lock_active=True)

            self._receiver_lock.release_write()

        def connection_lost(self, exc):
            Logger.get_instance().error("Networking card exception:" + str(exc))
            raise IOError("Connection to quantum networking card lost!")

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if EmulationBackend.Hosts.__instance is not None:
                return EmulationBackend.Hosts.__instance
            else:
                return EmulationBackend.Hosts()

        def __init__(self):
            if EmulationBackend.Hosts.__instance is not None:
                raise Exception("Call get instance to get this class!")
            EmulationBackend.Hosts.__instance = self
            SafeDict.__init__(self)

    def __init__(self):
        self._networking_card = EmulationBackend.NetworkingCard.get_instance()
        self._hosts = EmulationBackend.Hosts.get_instance()

    def _send_to_networking_card(self, command, object):
        binary = b''
        binary += Serialization.integer_to_binary(command, 1)
        binary += object.to_binary()
        self._networking_card.send_bytestring(binary)

    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.
        """
        pass

    def stop(self):
        """
        Stops Backends which are running in an own thread or process.
        """
        pass

    def add_host(self, host):
        """
        Adds a host to the backend.

        Args:
            host (Host): New Host which should be added.
        """
        if isinstance(host.host_id, (bytes, bytearray)):
            raise ValueError("Host names have to be bytes for the emulation Backend!")
        if len(host.host_id) > 8:
            raise ValueError("Lenght of host id should not be more than 8 bytes!")
        self._hosts.add_to_dict(host.host_id, host)

    def send_packet_to_network(self, packet):
        """
        Takes a network packet and sends it to the network to be processed there.

        Args:
            packet (Packet): packet object to be send to the network.
        """
        self._send_to_networking_card(Serialization.Commands.SEND_NETWORK_PACKET, packet)

    def create_qubit(self, host_id, id=None):
        """
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Reurns:
            Qubit of backend type.
        """
        if id is None:
            id = uuid.uuid4().bytes
        self._send_to_networking_card(Serialization.Commands.NEW_QUBIT, NewQubit(id))
        return id

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        """
        # happens in the network layer
        raise EnvironmentError("This function is not implemented for this \
                        backend type!")

    def create_EPR(self, host_id, q_id=None, block=False):
        """
        Creates an EPR pair for two qubits and returns both of the qubits.

        Args:
            host_id (String): ID of the host who creates the EPR state.
            q_id (String): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Returns both EPR qubits.
        """
        id1 = uuid.uuid4().bytes
        id2 = uuid.uuid4().bytes
        # use EPR creation acceleration hardware of quantum networking card
        CreateEntangledPair(id1, id2)
        self._send_to_networking_card(Serialization.Commands.CREATE_ENTANGLED_PAIR,\
                                      CreateEntangledPair(id1, id2))
        host = self._hosts.get_from_dict(host_id)
        q1 = Qubit(host, qubit=id1, q_id=q_id, blocked=block)
        q2 = Qubit(host, qubit=id2, q_id=q_id, blocked=block)
        return q1, q2

    ##########################
    #   Gate definitions    #
    #########################

    def _apply_single_gate(self, qubit, gate, gate_parameter=0):
        self._send_to_networking_card(Serialization.Commands.APPLY_GATE_SINGLE_GATE,\
                            SingleGate(qubit.qubit, gate, gate_parameter))

    def _apply_double_gate(self, qubit1, qubit2, gate):
        self._send_to_networking_card(Serialization.Commands.APPLY_DOUBLE_GATE,\
                            DoubleGate(qubit1.qubit, qubit2.qubit, gate, 0))

    def I(self, qubit):
        """
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.Idenitity)

    def X(self, qubit):
        """
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.X)

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.Y)

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.Z)

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.H)

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.T)

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.RX, phi)

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.RY, phi)

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, Serialization.SingleGates.RZ, phi)

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        self._apply_double_gate(qubit, target, Serialization.DoubleGates.CNOT)

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        self._apply_double_gate(qubit, target, Serialization.DoubleGates.CPHASE)

    def custom_gate(self, qubit, gate):
        """
        Applies a custom gate to the qubit.

        Args:
            qubit(Qubit): Qubit to which the gate is applied.
            gate(np.ndarray): 2x2 array of the gate.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_controlled_gate(self, qubit, target, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit(Qubit): Qubit to control the gate.
            target(Qubit): Qubit on which the gate is applied.
            gate(nd.array): 2x2 array for the gate applied to target.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_controlled_two_qubit_gate(self, qubit, target_1, target_2, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit (Qubit): Qubit to control the gate.
            target_1 (Qubit): Qubit on which the gate is applied.
            target_2 (Qubit): Qubit on which the gate is applied.
            gate (nd.array): 4x4 array for the gate applied to target.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_two_qubit_gate(self, qubit1, qubit2, gate):
        """
        Applies a custom two qubit gate to qubit1 \\otimes qubit2.

        Args:
            qubit1(Qubit): First qubit of the gate.
            qubit2(Qubit): Second qubit of the gate.
            gate(np.ndarray): 4x4 array for the gate applied.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def density_operator(self, qubit):
        """
        Returns the density operator of this qubit. If the qubit is entangled,
        the density operator will be in a mixed state.

        Args:
            qubit (Qubit): Qubit of the density operator.

        Returns:
            np.ndarray: The density operator of the qubit.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def measure(self, qubit, non_destructive):
        """
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.
            non_destructive (bool): Determines if the Qubit should stay in the
                                    system or be eliminated.

        Returns:
            The value which has been measured.
        """
        queue = Queue()
        self._networking_card.add_notify_on_recv(queue,
                                Serialization.NetworkCommands.MEASUREMENT_RESULT,
                                qubit.qubit)
        self._send_to_networking_card(Serialization.Commands.MEASURE,\
                    Measure(qubit.qubit, non_destructive))
        meas_res = queue.get()
        return meas_res.result

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        _ = self.measure(qubit, False)
        return
