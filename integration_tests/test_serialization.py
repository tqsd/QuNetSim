import unittest
from qunetsim.backends.emulated_backend import create_binary_frame
from qunetsim.utils.constants import Constants
from qunetsim.utils.serialization import Serialization


# @unittest.skip('')
class TestSerialization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # @unittest.skip('')
    def test_recover_host_id(self):
        host_id = "Alice"

        binary = Serialization.host_id_to_binary(host_id)

        self.assertTrue(len(binary) == Serialization.SIZE_HOST_ID)

        recovered_host_id = Serialization.binary_to_host_id(binary)

        self.assertEqual(host_id, recovered_host_id)

    def test_recover_bitfield(self):
        frame = [["1", 0, 1],
                 ["2", 0, 1],
                 ["3", 0, 1],
                 ["4", 0, 1],
                 ["5", 1, 1],
                 ["6", 1, 1],
                 ["7", 1, 1],
                 ["8", 1, 1]]
        binary = create_binary_frame(frame)

        self.assertTrue(len(binary) == 1)

        for nr in range(0, 4):
            opt = Serialization.binary_extract_option_field(binary, nr)
            self.assertTrue(opt is False)

        for nr in range(4, 8):
            opt = Serialization.binary_extract_option_field(binary, nr)
            self.assertTrue(opt is True, "Wrong result for %d." % nr)
