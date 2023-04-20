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
        host.add_qubit('C', q2)
        host.add_ghz_qubit('D', q3)

        host2.add_qubit('A', q4)

        # Test all types of qubits
        self.assertEqual(q1, host.get_qubit_by_id(q1.id))
        self.assertEqual(q2, host.get_qubit_by_id(q2.id))
        self.assertEqual(q3, host.get_qubit_by_id(q3.id))

        # Test getting qubits from other hosts
        self.assertIsNone(host.get_qubit_by_id(q4.id))

        # Test getting qubits that don't exist
        self.assertIsNone(host.get_qubit_by_id('fake'))

    def test_get_data_qubit(self):
        with self.assertWarns(DeprecationWarning):
            host = Host('A')
            q1 = Qubit(host)

            host.add_qubit('A', q1)

            qs = host.get_data_qubit('A')
            self.assertIsInstance(qs, Qubit)

    def test_get_qubit(self):
        host = Host('A')
        q1 = Qubit(host)

        host.add_qubit('A', q1)

        qs = host.get_qubit('A')
        self.assertIsInstance(qs, Qubit)

    def test_get_data_qubits(self):
        with self.assertWarns(DeprecationWarning):
            host = Host('A')
            q1 = Qubit(host)
            q2 = Qubit(host)
            q3 = Qubit(host)

            host.add_qubit('B', q1)

            qs = host.get_data_qubits('B')
            self.assertEqual(len(qs), 1)

            host.add_qubit('B', q2)
            host.add_qubit('B', q3)

            qs = host.get_data_qubits('B')
            self.assertEqual(len(qs), 3)

            qs = host.get_data_qubits('B', remove_from_storage=True)
            self.assertEqual(len(qs), 3)

            qs = host.get_data_qubits('B', remove_from_storage=True)
            self.assertEqual(len(qs), 0)

    def test_get_qubits(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host.add_qubit('B', q1)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 1)

        host.add_qubit('B', q2)
        host.add_qubit('B', q3)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 3)

        qs = host.get_qubits('B', remove_from_storage=True)
        self.assertEqual(len(qs), 3)

        qs = host.get_qubits('B', remove_from_storage=True)
        self.assertEqual(len(qs), 0)

    def test_resetting_qubits(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host.add_epr('B', q1)
        host.add_qubit('B', q2)
        host.add_ghz_qubit('B', q3)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 1)

        host.reset_data_qubits('B')
        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 0)

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

    def test_add_connections(self):
        a = Host('A')

        a.add_connection('B')
        self.assertEqual(len(a.classical_connections), 1)
        self.assertEqual(len(a.quantum_connections), 1)

        a.add_c_connection('C')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 1)

        a.add_q_connection('D')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 2)

        a.add_connections(['E', 'F'])
        self.assertEqual(len(a.classical_connections), 4)
        self.assertEqual(len(a.quantum_connections), 4)

        a.add_c_connections(['G', 'H'])
        self.assertEqual(len(a.classical_connections), 6)
        self.assertEqual(len(a.quantum_connections), 4)

        a.add_q_connections(['I', 'J'])
        self.assertEqual(len(a.classical_connections), 6)
        self.assertEqual(len(a.quantum_connections), 6)

    def test_remove_connections(self):
        a = Host('A')
        a.add_connections(['B', 'C'])
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 2)
        a.remove_q_connection('B')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 1)
        a.remove_c_connection('B')
        self.assertEqual(len(a.classical_connections), 1)
        self.assertEqual(len(a.quantum_connections), 1)
        a.remove_connection('C')
        self.assertEqual(len(a.classical_connections), 0)
        self.assertEqual(len(a.quantum_connections), 0)
        a.remove_connection('C')
        self.assertEqual(len(a.classical_connections), 0)
        self.assertEqual(len(a.quantum_connections), 0)
