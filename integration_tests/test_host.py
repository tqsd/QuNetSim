import unittest

from qunetsim.objects import Qubit
from qunetsim.components import Host
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

    def test_get_qubits_by_id(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host2 = Host('B')
        q4 = Qubit(host2)

        host.add_epr('B', q1)
        host.add_data_qubit('C', q2)
        host.add_ghz_qubit('D', q3)

        host2.add_data_qubit('A', q4)

        # Test all types of qubits
        self.assertEqual(q1, host.get_qubit_by_id(q1.id))
        self.assertEqual(q2, host.get_qubit_by_id(q2.id))
        self.assertEqual(q3, host.get_qubit_by_id(q3.id))

        # Test getting qubits from other hosts
        self.assertIsNone(host.get_qubit_by_id(q4.id))

        # Test getting qubits that don't exist
        self.assertIsNone(host.get_qubit_by_id('fake'))

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
