import unittest
import uuid

from qunetsim.objects import QuantumStorage
from qunetsim.utils.constants import Constants


class FakeQubit(object):
    """
    A qubit object that has fewer properties to test quantum storage.
    """

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
class TestQuantumStorage(unittest.TestCase):
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
        purpose = "data"
        storage = QuantumStorage()

        # STORAGE_LIMIT_ALL mode test
        storage.storage_limit_mode = QuantumStorage.STORAGE_LIMIT_ALL
        storage.storage_limit = 10
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purpose, str(c))
        self.assertEqual(storage.amount_qubits_stored, 10)

        # STORAGE_LIMIT_PER_HOST mode test
        storage = QuantumStorage()
        storage.storage_limit_mode = QuantumStorage.STORAGE_LIMIT_PER_HOST
        storage.storage_limit = 10
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purpose, str(1))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purpose, str(2))
        self.assertEqual(storage.amount_qubits_stored, 20)

        # STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode test
        storage = QuantumStorage()
        storage.storage_limit_mode = QuantumStorage.STORAGE_LIMIT_INDIVIDUALLY_PER_HOST
        storage.set_storage_limit_with_host(10, str(1))
        storage.set_storage_limit_with_host(12, str(2))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purpose, str(1))
        for c in range(15):
            q = FakeQubit()
            storage.add_qubit_from_host(q, purpose, str(2))
        self.assertEqual(storage.amount_qubits_stored, 22)

    def test_change_id_of_qubits(self):
        purpose = "data"
        storage = QuantumStorage()

        for c in range(15):
            q = FakeQubit(c)
            storage.add_qubit_from_host(q, purpose, 'Bob')

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

    def test_get_qubit_by_id(self):
        q1 = FakeQubit()
        q2 = FakeQubit()
        q3 = FakeQubit()

        storage = QuantumStorage()
        storage.add_qubit_from_host(q1, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q2, from_host_id='T', purpose=Constants.EPR)
        storage.add_qubit_from_host(q3, from_host_id='V', purpose=Constants.GHZ)

        self.assertEqual(q1, storage.get_qubit_by_id(q1.id))
        self.assertEqual(q2, storage.get_qubit_by_id(q2.id))
        self.assertEqual(q3, storage.get_qubit_by_id(q3.id))

    def test_amount_qubits_from_host(self):
        q1 = FakeQubit()
        q2 = FakeQubit()
        q3 = FakeQubit()
        q4 = FakeQubit()

        storage = QuantumStorage()
        storage.add_qubit_from_host(q1, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q2, from_host_id='T', purpose=Constants.EPR)
        storage.add_qubit_from_host(q3, from_host_id='V', purpose=Constants.GHZ)

        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 1)
        self.assertEqual(storage.amount_qubits_stored_with_host('T'), 1)
        self.assertEqual(storage.amount_qubits_stored_with_host('V'), 1)

        storage.add_qubit_from_host(q4, from_host_id='S', purpose=Constants.DATA)
        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 2)

    def test_reset_qubits_from_host(self):
        q1 = FakeQubit()
        q2 = FakeQubit()
        q3 = FakeQubit()

        storage = QuantumStorage()
        storage.add_qubit_from_host(q1, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q2, from_host_id='T', purpose=Constants.EPR)
        storage.add_qubit_from_host(q3, from_host_id='V', purpose=Constants.GHZ)

        storage.reset_qubits_from_host('S')
        self.assertEqual(storage.amount_qubits_stored, 2)
        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('T'), 1)
        self.assertEqual(storage.amount_qubits_stored_with_host('V'), 1)

        storage.reset_qubits_from_host('T')
        self.assertEqual(storage.amount_qubits_stored, 1)
        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('T'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('V'), 1)

        storage.reset_qubits_from_host('V')
        self.assertEqual(storage.amount_qubits_stored, 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('T'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('V'), 0)

    def test_reset_all_qubits(self):
        q1 = FakeQubit()
        q2 = FakeQubit()
        q3 = FakeQubit()

        storage = QuantumStorage()
        storage.add_qubit_from_host(q1, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q2, from_host_id='T', purpose=Constants.EPR)
        storage.add_qubit_from_host(q3, from_host_id='V', purpose=Constants.GHZ)

        storage.reset_storage()
        self.assertEqual(storage.amount_qubits_stored, 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('S'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('T'), 0)
        self.assertEqual(storage.amount_qubits_stored_with_host('V'), 0)

    def test_get_all_data_qubits_from_host(self):
        q1 = FakeQubit()
        q2 = FakeQubit()
        q3 = FakeQubit()

        storage = QuantumStorage()
        storage.add_qubit_from_host(q1, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q2, from_host_id='S', purpose=Constants.DATA)
        storage.add_qubit_from_host(q3, from_host_id='S', purpose=Constants.DATA)

        qubits = storage.get_all_qubits_from_host('S', remove=False)
        self.assertEqual(len(qubits), 3)
        qubits = storage.get_all_qubits_from_host('S', remove=False)
        self.assertEqual(len(qubits), 3)
        qubits = storage.get_all_qubits_from_host('S', purpose=Constants.EPR, remove=False)
        self.assertEqual(len(qubits), 0)
        qubits = storage.get_all_qubits_from_host('S', remove=True)
        self.assertEqual(len(qubits), 3)
        qubits = storage.get_all_qubits_from_host('S', remove=True)
        self.assertEqual(len(qubits), 0)
