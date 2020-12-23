import enum
from qunetsim.utils.constants import Constants

class Serialization:
    BYTEORDER = 'big'

    class Commands(enum.Enum):
        IDLE = 0
        APPLY_GATE_SINGLE_GATE = 1
        APPLY_DOUBLE_GATE = 2
        MEASURE = 3
        NEW_QUBIT = 4
        SEND_QUBIT = 5
        CREATE_ENTANGLED_PAIR = 6
        SEND_NETWORK_PACKET = 7

    class NetworkCommands(enum.Enum):
        IDLE = 0
        MEASUREMENT_RESULT = 1
        RECV_NETWORK_PACKET = 2

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

    class PayloadTypes(enum.Enum):
        SIGNAL = 0
        CLASSICAL = 1
        QUANTUM = 2

    # Length definitions in byte
    SIZE_HOST_ID = 8
    SIZE_SEQUENCE_NR = 8
    SIZE_QUBIT_ID = 16
    SIZE_QUNETSIM_QUBIT_ID = 50
    SIZE_MSG_CONTENT = 512
    SIZE_PROTOCOL = 1
    SIZE_PAYLOAD_TYPE = 1
    SIZE_OPTIONS = 1                # generic size for option fields

    ###########################################################
    # To binary
    ###########################################################
    def string_to_binary(string, bytesize):
        if len(string) > bytesize:
            raise ValueError("The host id is too long.")
        binary_string = str.encode(string)
        binary_string += int.to_bytes(0, bytesize-len(string), Serialization.BYTEORDER)
        return binary_string

    def host_id_to_binary(host_id):
        return Serialization.string_to_binary(host_id, Serialization.SIZE_HOST_ID)

    def msg_content_to_binary(content):
        return Serialization.string_to_binary(content, Serialization.SIZE_MSG_CONTENT)

    ###########################################################
    # From binary
    ###########################################################
    def binary_to_string(binary_string):
        string = binary_string.decode()
        return string.rstrip('\x00')

    def binary_to_host_id(binary_string):
        return Serialization.binary_to_string(binary_string)

    def binary_to_payload_type(binary_string):
        payload_nr = Serialization.binary_to_integer(binary_string)
        if payload_nr == Serialization.PayloadTypes.SIGNAL.value:
            return Constants.SIGNAL
        elif payload_nr == Serialization.PayloadTypes.CLASSICAL.value:
            return Constants.CLASSICAL
        elif payload_nr == Serialization.PayloadTypes.QUANTUM.value:
            return Constants.QUANTUM
        raise ValueError("Udefined payload type received!")

    def binary_to_integer(binary_string):
        return int.from_bytes(binary_string, Serialization.BYTEORDER)

    def binary_extract_option_field(binary_string, position):
        """
        Extract a boolean from a option field.

        Args:
            binary_string: The 8 bit binary string
            position: The position in the string, starting with 0.
        """
        binary = Serialization.binary_to_integer(binary_string)
        val = (binary & (0x1 << position)) >> position
        if val:
            return True
        return False
