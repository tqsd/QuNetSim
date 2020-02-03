import uuid
import sys

sys.path.append("../..")
from objects.quantum_storage import *

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


def test_store_and_recover():
    storage = QuantumStorage()
    q = FakeQubit()
    id = q.id
    host_id = "Alice"
    purp = "data"

    print("Start test store and recover...")

    assert storage.amount_qubits_stored == 0
    storage.add_qubit_from_host(q, purp, host_id)
    assert storage.amount_qubits_stored == 1
    q2 = storage.get_qubit_from_host(host_id, id, purpose=purp)
    assert storage.amount_qubits_stored == 0
    assert q == q2

    q2 = storage.get_qubit_from_host(host_id, id, purpose=purp)
    assert q2 == None

    storage.add_qubit_from_host(q, purp, host_id)
    q2 = storage.get_qubit_from_host(host_id, purpose=purp)
    assert storage.amount_qubits_stored == 0
    assert q == q2

    print("Test store and recover was successfull!")

def test_change_host():
    storage = QuantumStorage()
    q = FakeQubit()
    id = q.id
    host_id1 = "Alice"
    host_id2 = "Bob"
    purp = "data"

    print("Start test store and recover...")

    assert storage.amount_qubits_stored == 0
    storage.add_qubit_from_host(q, purp, host_id1)
    assert storage.amount_qubits_stored == 1
    q2 = storage.get_qubit_from_host(host_id1, id)
    storage.add_qubit_from_host(q2, purp, host_id2)
    assert storage.amount_qubits_stored == 1

    q2 = storage.get_qubit_from_host(host_id1, id)
    assert q2 == None

    q2 = storage.get_qubit_from_host(host_id2)
    assert storage.amount_qubits_stored == 0
    assert q == q2

    print("Test store and recover was successfull!")

def test_storage_limits():
    purp = "data"
    print("Start storage limit test...")
    storage = QuantumStorage()
    print("Start test for STORAGE_LIMIT_ALL mode...")
    storage.set_storage_limit_mode(STORAGE_LIMIT_ALL)
    storage.set_storage_limit(10)
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, purp, str(c))
    assert(storage.amount_qubits_stored == 10)
    print("STORAGE_LIMIT_ALL mode was successfull!")

    print("Start test for STORAGE_LIMIT_PER_HOST mode...")
    storage = QuantumStorage()
    storage.set_storage_limit_mode(STORAGE_LIMIT_PER_HOST)
    storage.set_storage_limit(10)
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, purp, str(1))
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, purp, str(2))
    assert(storage.amount_qubits_stored == 20)
    print("STORAGE_LIMIT_PER_HOST mode was successfull!")

    print("Start test for STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode...")
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
    assert(storage.amount_qubits_stored == 22)
    print("STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode was successfull!")

    print("Storage limit test was successfull!")

def test_change_id_of_qubits():
    purp = "data"
    print("Start change id of qubit test...")
    storage = QuantumStorage()

    for c in range(15):
        q = FakeQubit(c)
        storage.add_qubit_from_host(q, purp, 'Bob')

    search_id = str(10)
    new_id = str(101)
    old_id = storage.change_qubit_id('Bob', new_id, search_id)

    assert old_id == search_id

    q1 = storage.get_qubit_from_host('Bob', search_id)
    assert q1 == None

    q2 = storage.get_qubit_from_host('Bob', new_id)

    assert q2 != None

    new_id2 = str(102)
    old_id = storage.change_qubit_id('Bob', new_id2)
    assert int(old_id) < 15
    q1 = storage.get_qubit_from_host('Bob', old_id)
    assert q1 == None
    q2 = storage.get_qubit_from_host('Bob', new_id2)
    assert q2 != None

    print("Change id of qubit test was successfull!")


if __name__ == "__main__":
    test_store_and_recover()
    test_change_host()
    test_storage_limits()
    test_change_id_of_qubits()
