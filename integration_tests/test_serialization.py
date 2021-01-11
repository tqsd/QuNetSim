import unittest
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
        binary = Serialization.options_to_binary(0, 0, 0, 0, 1, 1, 1, 1)

        self.assertTrue(len(binary) == 1)

        for nr in range(0, 4):
            opt = Serialization.binary_extract_option_field(binary, nr)
            self.assertTrue(opt is False)

        for nr in range(4, 8):
            opt = Serialization.binary_extract_option_field(binary, nr)
            self.assertTrue(opt is True, "Wrong result for %d." % nr)

    def test_recover_float(self):
        number = 2.25
        binary_number = Serialization.float_to_binary(number)

        # check that this is a 32 bit float
        self.assertTrue(len(binary_number) == Serialization.SIZE_FLOAT,\
                    "length is " + str(len(binary_number)) + ", " + str(binary_number))

        recovered_number = Serialization.binary_to_float(binary_number)

        self.assertEqual(number, recovered_number)
