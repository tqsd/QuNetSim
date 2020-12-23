import unittest
from qunetsim.objects import Packet
from qunetsim.objects import Qubit
from qunetsim.utils.constants import Constants
from qunetsim.utils.serialization import Serialization
import uuid

import qunetsim.backends.emulated_backend as back

# @unittest.skip('')
class TestEmulationBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_single_gate_frame_creation(self):
        id = uuid.uuid4().bytes
        frame = back.create_frame(Serialization.Commands.APPLY_GATE_SINGLE_GATE,
                                  qubit_id=id,
                                  gate=Serialization.SingleGates.H,
                                  gate_parameter=0)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)

        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    def test_double_gate_frame_creation(self):
        id = uuid.uuid4().bytes
        id2 = uuid.uuid4().bytes
        frame = back.create_frame(Serialization.Commands.APPLY_DOUBLE_GATE,
                                  first_qubit_id=id,
                                  second_qubit_id=id2,
                                  gate=Serialization.DoubleGates.CNOT,
                                  gate_parameter=0)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)

        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    def test_measure_frame_creation(self):
        id = uuid.uuid4().bytes
        frame = back.create_frame(Serialization.Commands.MEASURE,
                                  qubit_id=id,
                                  non_destructive=0)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)

        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    def test_new_qubit_frame_creation(self):
        id = uuid.uuid4().bytes
        frame = back.create_frame(Serialization.Commands.NEW_QUBIT,
                                  qubit_id=id)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)

        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    def test_create_epr_frame_creation(self):
        id = uuid.uuid4().bytes
        id2 = uuid.uuid4().bytes
        frame = back.create_frame(Serialization.Commands.CREATE_ENTANGLED_PAIR,
                                  first_qubit_id=id,
                                  second_qubit_id=id2)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)

        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    def test_create_packet_frame_creation_quantum(self):
        id = uuid.uuid4().bytes
        q = Qubit('A', qubit=id)
        packet = Packet('A', 'B', Constants.REC_EPR, Constants.QUANTUM, q)
        frame = back.network_packet_to_frame(packet)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)
        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]),
                        "Frame is %s" % str(frame))

    @unittest.skip('')
    def test_create_packet_frame_creation_signal(self):
        packet = Packet('A', 'B', Constants.REC_EPR, Constants.SIGNAL)
        frame = back.network_packet_to_frame(packet)
        self.assertTrue(None not in [x[1] for x in frame])

        binary_frame = back.create_binary_frame(frame)
        self.assertTrue(8 * len(binary_frame) == sum([x[2] for x in frame]))

    @unittest.skip('')
    def test_multiple_backends(self):
        pass

    @unittest.skip('')
    def test_adding_hosts_to_backend(self):
        pass
