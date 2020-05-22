import unittest
import uuid

from objects.quantum_storage import QuantumStorage, STORAGE_LIMIT_ALL,\
                                    STORAGE_LIMIT_PER_HOST,\
                                    STORAGE_LIMIT_INDIVIDUALLY_PER_HOST

class FakeQubit(object):

    def __init__(self, id=None):
        if id is not None:
            self.id = str(id)
        else:
            self.id = str(uuid.uuid4())

    def release(self):
        pass

    def set_new_id(self, id):
        self.id = id

    def __str__(self):
        return "Qubit with id %s" % self.id

# @unittest.skip('')
class TestClassicalStorage(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # @unittest.skip('')
    def test_store_and_recover(self):
        storage = QuantumStorage()
        q = FakeQubit()
        id = q.id
        host_id = "Alice"
        purp = "data"

        self.assertEqual(storage.amount_qubits_stored, 0)
        storage.add_qubit_from_host(q, purp, host_id)
        self.assertEqual(storage.amount_qubits_stored, 1)
        q2 = storage.get_qubit_from_host(host_id, id, purpose=purp)
        self.assertEqual(storage.amount_qubits_stored, 0)
        self.assertEqual(q, q2)

        q2 = storage.get_qubit_from_host(host_id, id, purpose=purp)
        self.assertEqual(q2, None)

        storage.add_qubit_from_host(q, purp, host_id)
        q2 = storage.get_qubit_from_host(host_id, purpose=purp)
        self.assertEqual(storage.amount_qubits_stored, 0)
        self.assertEqual(q, q2)

    # @unittest.skip('')
    def test_change_host(self):
        storage = QuantumStorage()
        q = FakeQubit()
        id = q.id
        host_id1 = "Alice"
        host_id2 = "Bob"
        purp = "data"

        self.assertEqual(storage.amount_qubits_stored, 0)
        storage.add_qubit_from_host(q, purp, host_id1)
        self.assertEqual(storage.amount_qubits_stored, 1)
        q2 = storage.get_qubit_from_host(host_id1, id)
        storage.add_qubit_from_host(q2, purp, host_id2)
        self.assertEqual(storage.amount_qubits_stored, 1)

        q2 = storage.get_qubit_from_host(host_id1, id)
        self.assertEqual(q2, None)

        q2 = storage.get_qubit_from_host(host_id2)
        self.assertEqual(storage.amount_qubits_stored, 0)
        self.assertEqual(q, q2)

    # @unittest.skip('')
    def test_storage_limits(self):
        purp = "data"
        storage = QuantumStorage()

        # STORAGE_LIMIT_ALL mode test
        storage.set_storage_limit_mode(STORAGE_LIMIT_ALL)
        storage.set_storage_limit(10)
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purp, str(c))
        self.assertEqual(storage.amount_qubits_stored, 10)

        # STORAGE_LIMIT_PER_HOST mode test
        storage = QuantumStorage()
        storage.set_storage_limit_mode(STORAGE_LIMIT_PER_HOST)
        storage.set_storage_limit(10)
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purp, str(1))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purp, str(2))
        self.assertEqual(storage.amount_qubits_stored, 20)

        # STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode test
        storage = QuantumStorage()
        storage.set_storage_limit_mode(STORAGE_LIMIT_INDIVIDUALLY_PER_HOST)
        storage.set_storage_limit(10, str(1))
        storage.set_storage_limit(12, str(2))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purp, str(1))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purp, str(2))
        self.assertEqual(storage.amount_qubits_stored, 22)

    def test_change_id_of_qubits(self):
        purp = "data"
        storage = QuantumStorage()

        for c in range(15):
            q = FakeQubit(c)
            storage.add_qubit_from_host(q, purp, 'Bob')

        search_id = str(10)
        new_id = str(101)
        old_id = storage.change_qubit_id('Bob', new_id, search_id)

        self.assertEqual(old_id, search_id)

        q1 = storage.get_qubit_from_host('Bob', search_id)
        self.assertEqual(q1, None)

        q2 = storage.get_qubit_from_host('Bob', new_id)

        self.assertNotEqual(q2, None)

        new_id2 = str(102)
        old_id = storage.change_qubit_id('Bob', new_id2)
        self.assertTrue(int(old_id) < 15)
        q1 = storage.get_qubit_from_host('Bob', old_id)
        self.assertEqual(q1, None)
        q2 = storage.get_qubit_from_host('Bob', new_id2)
        self.assertNotEqual(q2, None)
