from qunetsim.utils.serialization import Serialization
from qunetsim.objects.logger import Logger
import uuid


class SingleGate(object):

    @staticmethod
    def from_binary(binary_string):
        # get binary parts from the binary string
        start = 0
        qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        gate = binary_string[start:(start+Serialization.SIZE_GATE)]
        start += Serialization.SIZE_GATE
        gate_parameter = binary_string[start:(start+Serialization.SIZE_GATE_PARAMETER)]
        start += Serialization.SIZE_GATE_PARAMETER

        # turn binary data to QuNetSim data
        gate = Serialization.binary_to_integer(gate)
        gate_parameter = Serialization.binary_to_float(gate_parameter)

        return SingleGate(qubit_id, gate, gate_parameter)

    def __init__(self, qubit_id, gate, gate_parameter):
        self.qubit_id = qubit_id
        self.gate = gate
        self.gate_parameter = gate_parameter

    def to_binary(self):
        binary_string = b''
        binary_string += self.qubit_id
        binary_string += Serialization.integer_to_binary(self.gate, Serialization.SIZE_GATE)
        binary_string += Serialization.float_to_binary(self.gate_parameter)
        return binary_string


class DoubleGate(object):

    @staticmethod
    def from_binary(binary_string):
        # get binary parts from the binary string
        start = 0
        first_qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        second_qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        gate = binary_string[start:(start+Serialization.SIZE_GATE)]
        start += Serialization.SIZE_GATE
        gate_parameter = binary_string[start:(start+Serialization.SIZE_GATE_PARAMETER)]
        start += Serialization.SIZE_GATE_PARAMETER

        # turn binary data to QuNetSim data
        gate = Serialization.binary_to_integer(gate)
        gate_parameter = Serialization.binary_to_float(gate_parameter)

        return SingleGate(first_qubit_id, second_qubit_id, gate, gate_parameter)

    def __init__(self, first_qubit_id, second_qubit_id, gate, gate_parameter):
        self.first_qubit_id = first_qubit_id
        self.second_qubit_id = second_qubit_id
        self.gate = gate
        self.gate_parameter = gate_parameter

    def to_binary(self):
        binary_string = b''
        binary_string += self.first_qubit_id
        binary_string += self.second_qubit_id
        binary_string += Serialization.integer_to_binary(self.gate, Serialization.SIZE_GATE)
        binary_string += Serialization.float_to_binary(self.gate_parameter)
        return binary_string


class Measure(object):

    @staticmethod
    def from_binary(binary_string):
        # get binary parts from the binary string
        start = 0
        qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        options = binary_string[start:(start+Serialization.SIZE_OPTIONS)]
        start += Serialization.SIZE_OPTIONS

        # turn binary data to QuNetSim data
        non_destructive = Serialization.binary_extract_option_field(options, 0)

        return Measure(qubit_id, non_destructive)

    def __init__(self, qubit_id, non_destructive):
        self.qubit_id = qubit_id
        self.non_destructive = non_destructive

    def to_binary(self):
        binary_string = b''
        binary_string += self.qubit_id
        binary_string += Serialization.options_to_binary(self.non_destructive)
        return binary_string


class MeasurementResult(object):

    @staticmethod
    def from_binary(binary_string):
        # get the binary parts from the binary string
        start = 0
        id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        options = binary_string[start:(start+Serialization.SIZE_OPTIONS)]
        start += Serialization.SIZE_OPTIONS

        # turn binary data to python data
        result = Serialization.binary_extract_option_field(options, 0)

        return MeasurementResult(id, result)

    def __init__(self, id, result):
        if isinstance(id, str):
            self.id = uuid.UUID(id)
        else:
            self.id = uuid.UUID(bytes=id)
        if result:
            self.result = 1
        else:
            self.result = 0

    def to_binary(self):
        binary_string = b''
        binary_string += self.id.bytes
        binary_string += Serialization.options_to_binary(self.result)
        return binary_string


class NewQubit(object):

    @staticmethod
    def from_binary(binary_string):
        # get binary parts from the binary string
        start = 0
        qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID

        Logger.get_instance().log("here")

        return NewQubit(qubit_id)

    def __init__(self, qubit_id):
        self.qubit_id = qubit_id

    def to_binary(self):
        binary_string = b''
        binary_string += self.qubit_id
        return binary_string


class CreateEntangledPair(object):

    @staticmethod
    def from_binary(binary_string):
        start = 0
        first_qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID
        second_qubit_id = binary_string[start:(start+Serialization.SIZE_QUBIT_ID)]
        start += Serialization.SIZE_QUBIT_ID

        return CreateEntangledPair(first_qubit_id, second_qubit_id)

    def __init__(self, first_qubit_id, second_qubit_id):
        self.first_qubit_id = first_qubit_id
        self.second_qubit_id = second_qubit_id

    def to_binary(self):
        binary_string = b''
        binary_string += self.first_qubit_id
        binary_string += self.second_qubit_id
        return binary_string
