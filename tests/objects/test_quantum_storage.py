import uuid
import sys

sys.path.append("../..")
from objects.quantum_storage import *

class FakeQubit(object):

    def __init__(self, id=None):
        if id is not None:
            self.id = id
        else:
            self.id = str(uuid.uuid4())

    def release(self):
        pass


def test_store_and_recover():
    storage = QuantumStorage()
    q = FakeQubit()
    id = q.id
    host_id = "Alice"

    print("Start test store and recover...")

    assert storage.amount_qubits_stored == 0
    storage.add_qubit_from_host(q, host_id)
    assert storage.amount_qubits_stored == 1
    q2 = storage.get_qubit_from_host(host_id, id)
    assert storage.amount_qubits_stored == 0
    assert q == q2

    storage.add_qubit_from_host(q, host_id)
    q2 = storage.get_qubit_from_host(host_id)
    assert storage.amount_qubits_stored == 0
    assert q == q2

    print("Test store and recover was successfull!")

def test_storage_limits():
    print("Start storage limit test...")
    storage = QuantumStorage()
    print("Start test for STORAGE_LIMIT_ALL mode...")
    storage.set_storage_limit_mode(STORAGE_LIMIT_ALL)
    storage.set_storage_limit(10)
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, str(c))
    assert(storage.amount_qubits_stored == 10)
    print("STORAGE_LIMIT_ALL mode was successfull!")

    print("Start test for STORAGE_LIMIT_PER_HOST mode...")
    storage = QuantumStorage()
    storage.set_storage_limit_mode(STORAGE_LIMIT_PER_HOST)
    storage.set_storage_limit(10)
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, str(1))
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, str(2))
    assert(storage.amount_qubits_stored == 20)
    print("STORAGE_LIMIT_PER_HOST mode was successfull!")

    print("Start test for STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode...")
    storage = QuantumStorage()
    storage.set_storage_limit_mode(STORAGE_LIMIT_INDIVIDUALLY_PER_HOST)
    storage.set_storage_limit(10, str(1))
    storage.set_storage_limit(12, str(2))
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, str(1))
    for c in range(15):
        q = FakeQubit()
        storage.add_qubit_from_host(q, str(2))
    assert(storage.amount_qubits_stored == 22)
    print("STORAGE_LIMIT_INDIVIDUALLY_PER_HOST mode was successfull!")

    print("Storage limit test was successfull!")



test_store_and_recover()
test_storage_limits()
