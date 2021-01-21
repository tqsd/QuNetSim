import struct
from qunetsim.utils.constants import Constants
from qunetsim.objects.logger import Logger


class Serialization:
    BYTEORDER = 'big'

    class Commands:
        IDLE = 0
        APPLY_GATE_SINGLE_GATE = 1
        APPLY_DOUBLE_GATE = 2
        MEASURE = 3
        NEW_QUBIT = 4
        SEND_QUBIT = 5
        CREATE_ENTANGLED_PAIR = 6
        SEND_NETWORK_PACKET = 7

    class NetworkCommands:
        IDLE = 0
        MEASUREMENT_RESULT = 1
        RECV_NETWORK_PACKET = 2

    class SingleGates:
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

    class DoubleGates:
        CNOT = 0
        CPHASE = 1

    class PayloadTypes:
        SIGNAL = 0
        CLASSICAL = 1
        QUANTUM = 2

    SIZE_FLOAT = 4

    # Length definitions in byte
    SIZE_HOST_ID = 8
    SIZE_SEQUENCE_NR = 8
    SIZE_QUBIT_ID = 16
    SIZE_QUNETSIM_QUBIT_ID = 50
    SIZE_MSG_CONTENT = 512
    SIZE_GATE = 1
    SIZE_GATE_PARAMETER = SIZE_FLOAT
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

    def integer_to_binary(integer, amount_of_bytes, signed=False):
        return integer.to_bytes(amount_of_bytes, byteorder=Serialization.BYTEORDER, signed=signed)

    def msg_content_to_binary(content):
        return Serialization.string_to_binary(content, Serialization.SIZE_MSG_CONTENT)

    def float_to_binary(num):
        return bytes(struct.pack('f', num))

    def options_to_binary(pos1, pos2=0, pos3=0, pos4=0, pos5=0, pos6=0, pos7=0, pos8=0):
        byte = 0
        byte = ((0x1 & int(pos1)) << 0) + ((0x1 & int(pos2)) << 1) + ((0x1 & int(pos3)) << 2)
        byte += ((0x1 & int(pos4)) << 3) + ((0x1 & int(pos5)) << 4) + ((0x1 & int(pos6)) << 5)
        byte += ((0x1 & int(pos7)) << 6) + ((0x1 & int(pos8)) << 7)
        return byte.to_bytes(1, byteorder=Serialization.BYTEORDER, signed=False)

    def payload_type_to_binary(payload_type):
        payload_number = None
        if payload_type == Constants.SIGNAL:
            payload_number = Serialization.PayloadTypes.SIGNAL
        elif payload_type == Constants.CLASSICAL:
            payload_number = Serialization.PayloadTypes.CLASSICAL
        elif payload_type == Constants.QUANTUM:
            payload_number = Serialization.PayloadTypes.QUANTUM
        else:
            raise ValueError("Unknow Payload type!")
        return Serialization.integer_to_binary(payload_number, Serialization.SIZE_PAYLOAD_TYPE)

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
        if payload_nr == Serialization.PayloadTypes.SIGNAL:
            return Constants.SIGNAL
        elif payload_nr == Serialization.PayloadTypes.CLASSICAL:
            return Constants.CLASSICAL
        elif payload_nr == Serialization.PayloadTypes.QUANTUM:
            return Constants.QUANTUM
        raise ValueError("Udefined payload type received!")

    def binary_to_integer(binary_string, signed=False):
        return int.from_bytes(binary_string, Serialization.BYTEORDER, signed=signed)

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

    def binary_to_float(binary):
        return struct.unpack('f', binary)[0]
