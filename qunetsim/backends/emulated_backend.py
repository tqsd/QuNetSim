from qunetsim.backends.rw_lock import RWLock
from qunetsim.objects.qubit import Qubit
from qunetsim.backends.safe_dict import SafeDict
from qunetsim.utils.constants import Constants
import uuid
from copy import deepcopy as dp
import enum
try:
    import serial
except ImportError:
    raise RuntimeError(" To use the Emulated Backend you need to install "
                       "pyserial!")


class Commands(enum.Enum):
    IDLE = 0
    APPLY_GATE_SINGLE_GATE = 1
    APPLY_DOUBLE_GATE = 2
    MEASURE = 3
    NEW_QUBIT = 4
    SEND_QUBIT = 5
    CREATE_ENTANGLED_PAIR = 6
    SEND_NETWORK_PACKET = 7


class SingleGates(enum.Enum):
    Idenitity = 0
    X = 1
    Y = 2
    Z = 3
    H = 4
    S = 5
    T = 6
    RX = 7
    RY = 8
    RZ = 9


class DoubleGates(enum.Enum):
    CNOT = 0
    CPHASE = 1


# Length definitions in byte
SIZE_HOST_ID = 8
SIZE_SEQUENCE_NR = 8
SIZE_QUBIT_ID = 16


####################################
#   Payload types
####################################
signal_payload = []
classical_payload = [["sender", None, SIZE_HOST_ID * 8],
                     ["sequence_number", None, SIZE_SEQUENCE_NR * 8],
                     ["message", None, 512 * 8]]
quantum_payload = [["qubit_id", None, SIZE_QUBIT_ID * 8]]

payload_type_to_payload = [signal_payload, classical_payload, quantum_payload]

calculate_bit_length = lambda x: sum([a[0] for a in x])

####################################
#    Frame Definitions
####################################
idle_frame = {}
single_gate_frame = [["qubit_id", None, SIZE_QUBIT_ID * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, 8]]
double_gate_frame = [["first_qubit_id", None, SIZE_QUBIT_ID * 8],
                     ["second_qubit_id", None, SIZE_QUBIT_ID * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, 8]]
measure_frame = [["qubit_id", None, SIZE_QUBIT_ID * 8],
                 ["non_destructive", None, 1],
                 ["reserved", 0, 7]]
new_qubit_frame = [["qubit_id", None, SIZE_QUBIT_ID * 8]]
send_qubit_frame = [["qubit_id", None, SIZE_QUBIT_ID * 8],
                    ["host_to_send_to", None, 64]]
create_epr_frame = [["first_qubit_id", None, SIZE_QUBIT_ID * 8],
                    ["second_qubit_id", None, SIZE_QUBIT_ID * 8]]
network_packet_frame = [["sender", None, SIZE_HOST_ID * 8],
                  ["receiver", None, SIZE_HOST_ID * 8],
                  ["sequence_number", None, SIZE_SEQUENCE_NR * 8],
                  ["protocol", None, 8],
                  ["payload_type", None, 8],
                  ["await_ack", None, 8],
                  ["payload", None, max([calculate_bit_length(x) for x in payload_type_to_payload])]]

Command_to_frame = [idle_frame, single_gate_frame, double_gate_frame,
                    measure_frame, new_qubit_frame, send_qubit_frame,
                    create_epr_frame]

command_basis_frame = [['command', None, 8]]


def create_binary_frame(dataframe, byteorder='big'):
    """
    Creates a binary string from a frame.
    """
    binary_output = b''

    def query_frame(frame, binary_string):
        bytecount = 0
        byte = 0
        for entry in dataframe:
            # Bitfields
            if bytecount != 0:
                if entry[2] + bytecount > 8:
                    raise ValueError("Bitfields have to count up to 8!")
                byte = (entry[1][str(bytecount)] & 0x1) << bytecount
                bytecount = bytecount + entry[2]
                if bytecount == 8:
                    binary_string = binary_string + byte.to_bytes(1, byteorder=byteorder, signed=False)
                    bytecount = 0

            if isinstance(entry[1], int):
                if entry[2] % 8 == 0:
                    binary_string = binary_string + entry[1].to_bytes(int(entry[2]/8), byteorder=byteorder, signed=False)
                else:
                    # start bitfield
                    byte = (entry[1][str(bytecount)] & 0x1) << bytecount
                    bytecount = bytecount + 1
            elif isinstance(entry[1], bytearray):
                if len(entry[1]) != int(entry[2]/8):
                    raise ValueError("Size of the binary string does not match the frame size!")
                binary_string = binary_string + entry[1]
            elif isinstance(entry[1], list):
                binary_string = binary_string + query_frame(entry[1], binary_string)
            else:
                raise ValueError("Unknown Type!")
        return binary_string

    return query_frame(dataframe, binary_output)


def create_frame(command, **kwargs):
    """
    Creates a frame with filled in information.
    """
    values = {}
    if command not in set(item.value for item in Commands):
        raise ValueError("Command does not exist!")
    values["command"] = command
    for key in kwargs.keys():
        if key not in values.keys():
            raise ValueError("This key does not exist!")
        values[key] = kwargs[key]
    frame = dp(command_basis_frame)
    frame = frame + dp(Command_to_frame[command])

    for entry in frame:
        entry[1] = values[entry[0]]

    return frame


def network_packet_to_frame(packet):

    def fill_payload(network_frame, payload):
        """
        Fills a payload into the network packet.
        """
        bit_length = network_frame[-1][2]
        bit_length_payload = calculate_bit_length(payload)
        del(network_frame[-1])
        for entry in payload:
            network_frame.append(entry)
        if bit_length > bit_length_payload:
            network_frame.append(["reserved", 0, bit_length - bit_length_payload])
        return network_frame

    frame = dp(network_packet_frame)
    values = {}

    payload = None
    if packet.payload_type == Constants.SIGNAL:
        payload = signal_payload
        values["payload_type"] = 0
    elif packet.payload_type == Constants.CLASSICAL:
        payload = classical_payload
        values["payload_type"] = 1
        values["qubit_id"] = packet.payload.id
    elif packet.payload_type == Constants.QUANTUM:
        payload = quantum_payload
        values["payload_type"] = 2
        values["message"] = packet.payload.content
    else:
        raise ValueError("This payload type does not exist!")

    frame = fill_payload(frame, payload)

    values["sender"] = packet.sender
    values["receiver"] = packet.receiver
    values["sequence_number"] = packet.seq_num
    values["protocol"] = packet.protocol
    values["await_ack"] = packet.await_ack

    return create_frame(Commands.SEND_NETWORK_PACKET, **values)


class EmulationBackend(object):
    """
    Backend which connects to a Quantum Networking Card.
    """

    class NetworkingCard(serial.threaded.Protocol):
        # There only should be one instance of NetworkingCard
        __instance = None

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
            ser = serial.Serial('/dev/ttyUSB0', 115200)
            self._listener_dict = SafeDict()
            self._notifier_list = []
            self._reader = serial.threaded.ReaderThread(ser, self)

        def __del__(self):
            self._reader.__exit__()

        def add_notify_on_recv(self, notify_me):
            """
            Add a function which should be called if certain data arrives.
            The data to be arrived is specified by TODO.
            """
            self._notifier_list.append(notify_me)

        def data_received(self, data):
            for notify_me in self._notifier_list:
                # Check if should be notified
                notify_me(data)

        def connection_lost(self, exc):
            return

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

    def _send_to_networking_card(self, frame):
        binary_string = create_binary_frame(frame)
        self._networking_card.send_bytestring(binary_string)

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
        frame = network_packet_to_frame(packet)
        self._send_to_networking_card(frame)

    def create_qubit(self, host_id):
        """
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Reurns:
            Qubit of backend type.
        """
        id = uuid.uuid4().bytes
        frame = create_frame(Commands.NEW_QUBIT.value, qubit_id=id)
        self._send_to_networking_card(frame)
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
        frame = create_frame(Commands.CREATE_ENTANGLED_PAIR, first_qubit_id=id1,
                             second_qubit_id=id2)
        self._send_to_networking_card(frame)
        host = self._hosts.get_from_dict(host_id)
        q1 = Qubit(host, qubit=id1, q_id=q_id, blocked=block)
        q2 = Qubit(host, qubit=id2, q_id=q_id, blocked=block)
        return q1, q2

    ##########################
    #   Gate definitions    #
    #########################

    def _apply_single_gate(self, qubit, gate, gate_parameter=0):
        frame = create_frame(Commands.APPLY_GATE_SINGLE_GATE, qubit_id=qubit.qubit,
                            gate=gate, gate_parameter=0)
        self._send_to_networking_card(frame)

    def _apply_double_gate(self, qubit1, qubit2, gate):
        frame = create_frame(Commands.APPLY_DOUBLE_GATE, first_qubit_id=qubit1.qubit,
                            second_qubit_id=qubit2.id, gate=gate)
        self._send_to_networking_card(frame)

    def I(self, qubit):
        """
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.Idenitity)

    def X(self, qubit):
        """
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.X)

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.Y)

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.Z)

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.H)

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self._apply_single_gate(qubit, SingleGates.T)

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, SingleGates.RX, phi)

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, SingleGates.RY, phi)

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        self._apply_single_gate(qubit, SingleGates.RZ, phi)

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        self._apply_double_gate(qubit, target, DoubleGates.CNOT)

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        self._apply_double_gate(qubit, target, DoubleGates.CPHASE)

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
        non_destructive_value = 0
        if non_destructive:
            non_destructive_value = 1
        frame = create_frame(Commands.MEASURE, qubit_id=qubit.qubit, non_destructive=non_destructive_value)
        self._send_to_networking_card(frame)
        # TODO wait for response
        raise EnvironmentError("Not implemented yet!")

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        _ = self.measure(qubit, False)
        return
