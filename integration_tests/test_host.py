import unittest
from qunetsim.components.host import Host
from random import randint


# @unittest.skip('')
class TestHost(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # @unittest.skip('')
    def test_connections(self):
        name = "A"
        neighbor = [str(x) for x in range(10)]
        a = Host(name)
        for x in neighbor:
            a.add_connection(x)

        connections = a.get_connections()
        for i in connections:
            self.assertTrue(i['connection'] in neighbor)
        a.backend.stop()

    # @unittest.skip('')
    def test_sequence_numbers(self):
        a = Host('A')
        neighbor = [str(x) for x in range(10)]
        random = [randint(0, 200) for _ in range(10)]
        for n, i in zip(neighbor, random):
            for _ in range(i):
                _ = a.get_next_sequence_number(n)

        for n, i in zip(neighbor, random):
            self.assertEqual(i, a.get_next_sequence_number(n))

        a.backend.stop()
