from qunetsim.backends.rw_lock import RWLock
from qunetsim.backends.safe_dict import SafeDict
from qunetsim.objects import Logger, Packet, Qubit
from qunetsim.utils.constants import Constants
from qunetsim.utils.serialization import Serialization
from qunetsim.utils.serialization.network_objects import SingleGate, DoubleGate,\
                                Measure, NewQubit, CreateEntangledPair, MeasurementResult
from qunetsim.components import Network, Host
from qunetsim.backends.emulated_backend import command_to_amount_of_bytes
import serial
import serial.threaded


def handle_binary(command, binary_string):
    if command == Serialization.Commands.IDLE:
        return None
    elif command == Serialization.Commands.APPLY_GATE_SINGLE_GATE:
        return SingleGate.from_binary(binary_string)
    elif command == Serialization.Commands.APPLY_DOUBLE_GATE:
        return DoubleGate.from_binary(binary_string)
    elif command == Serialization.Commands.MEASURE:
        return Measure.from_binary(binary_string)
    elif command == Serialization.Commands.NEW_QUBIT:
        return NewQubit.from_binary(binary_string)
    elif command == Serialization.Commands.SEND_QUBIT:
        raise ValueError("Command does not exist")
    elif command == Serialization.Commands.CREATE_ENTANGLED_PAIR:
        return CreateEntangledPair.from_binary(binary_string)
    elif command == Serialization.Commands.SEND_NETWORK_PACKET:
        return Packet.from_binary(binary_string)
    else:
        Logger.error("Unknown command!")


class NetworkingCard(serial.threaded.Protocol):
    IDLE_STATE = 0
    WAIT_FOR_DATA = 1

    def __init__(self, serial_path, host):
        ser = serial.Serial(serial_path, 115200)
        self._host = host
        self._listener_dict = SafeDict()
        self._receiver_lock = RWLock()  # to make sure that data is not read in parallel
        self._command_of_frame = 0  # description of the frame to be filled
        self._bytes_read_of_frame = 0  # bytes received of the current frame
        self._total_bytes_of_frame = 0  # total bytes in the frame currently receiving
        self._current_frame_bytes = None  # buffer for the bytes of the current frame
        self._receiver_state = NetworkingCard.IDLE_STATE
        self._reader = serial.threaded.ReaderThread(ser, self)

    def __del__(self):
        self._reader.__exit__()

    def _process_frame_data(self, data):
        if self._total_bytes_of_frame > (self._current_frame_bytes + len(data)):
            self._current_frame_bytes += len(data)
            self._total_bytes_of_frame += data
            return len(data)
        else:
            append_length = self._total_bytes_of_frame - self._current_frame_bytes
            data_append = data[:append_length]
            self._total_bytes_of_frame += data_append
            return append_length

    def _handle_finished_frame(self):
        object = handle_binary(self._command_of_frame, self._current_frame_bytes)
        if object is None:
            return  # IDLE command is not returned

        self._host.process_from_networking_card(object)

    def data_received(self, data, lock_active=False):
        if not lock_active:
            self._receiver_lock.acquire_write()

        if self._receiver_state == NetworkingCard.IDLE_STATE:
            self._receiver_state = NetworkingCard.WAIT_FOR_DATA
            self._command_of_frame, self._total_bytes_of_frame = command_to_amount_of_bytes(data[0])
            data = data[1:]  # remove command from the data
            self._current_frame_bytes = b''
            self._bytes_read_of_frame = 0

        if self._receiver_state == NetworkingCard.WAIT_FOR_DATA:
            amount_read = self._process_frame_data(data)
            if self._bytes_read_of_frame == self._total_bytes_of_frame:
                self._handle_finished_frame()
                self._receiver_state = NetworkingCard.IDLE_STATE
                self._bytes_read_of_frame = 0
                self._current_frame_bytes = None

            if amount_read < len(data):
                self.data_received(data[amount_read:])

        self._receiver_lock.release_write()

    def connection_lost(self, exc):
        raise IOError("Connection to quantum networking card lost!")


class SimulationHost(Host):

    def __init__(self, serial_path, *args, **kwargs):
        self.networking_card = NetworkingCard(serial_path)
        self.qubits = {}  # qubit id to qubit
        super(SimulationHost, self).__init__(*args, **kwargs)

    def rec_packet(self, packet):
        """
        Override receive packet of the Host class. Store the received qubit
        and send the packet to the real host.
        """
        if packet.payload_type == Constants.QUANTUM:
            self.qubits[packet.paylod.id] = packet.payload
        self.networking_card.send_bytestring(packet.to_binary())

    def process_from_networking_card(self, object):
        if isinstance(object, SingleGate):
            qubit = self.qubits[object.qubit_id]
            if object.gate == Serialization.SingleGates.H:
                qubit.H()
            elif object.gate == Serialization.SingleGates.X:
                qubit.X()
            elif object.gate == Serialization.SingleGates.Y:
                qubit.Y()
            elif object.gate == Serialization.SingleGates.Z:
                qubit.Z()
            elif object.gate == Serialization.SingleGates.S:
                qubit.S()
            elif object.gate == Serialization.SingleGates.T:
                qubit.T()
            elif object.gate == Serialization.SingleGates.RX:
                qubit.RX(object.gate_parameter)
            elif object.gate == Serialization.SingleGates.RY:
                qubit.RY(object.gate_parameter)
            elif object.gate == Serialization.SingleGates.RZ:
                qubit.RZ(object.gate_parameter)
            else:
                Logger.get_instance().error("Unknwon gate!")
        elif isinstance(object, DoubleGate):
            control_qubit = self.qubits[object.first_qubit_id]
            target_qubit = self.qubits[object.second_qubit_id]
            if object.gate == Serialization.DoubleGates.CNOT:
                control_qubit.cnot(target_qubit)
            elif object.gate == Serialization.DoubleGates.CPHASE:
                control_qubit.cphase(target_qubit)
            else:
                Logger.get_instance().error("Unknown gate!")
        elif isinstance(object, NewQubit):
            qubit = Qubit(self, q_id=object.qubit_id)
            self.qubits[object.qubit_id] = qubit
        elif isinstance(object, Measure):
            res = self.qubits[object.qubit_id].measure(object.non_destructive)
            if not object.non_destructive:
                del self.qubits[object.qubit_id]
            meas_res = MeasurementResult(object.qubit_id, res)
            self.networking_card.send_bytestring(meas_res.to_binary())
        elif isinstance(object, CreateEntangledPair):
            first_qubit_id = object.first_qubit_id
            second_qubit_id = object.second_qubit_id
            qubit1 = Qubit(self, q_id=first_qubit_id)
            qubit2 = Qubit(self, q_id=second_qubit_id)
            qubit1.H()
            qubit1.cnot(qubit2)
            self.qubits[object.first_qubit_id] = qubit1
            self.qubits[object.second_qubit_id] = qubit2
        elif isinstance(object, Packet):
            pass
        else:
            Logger.get_instance().error("%s: Unknow object type detected." % self.host_id)


class Simulator:
    def __init__(self, host_id_list, networking_card_path_list, backend):
        self.hosts = {}
        for host_id, serial_path in zip(host_id_list, networking_card_path_list):
            self.hosts[host_id] = SimulationHost(serial_path, host_id)
        self.network = Network()
        self.qubits = {}  # qubit id to qubit
