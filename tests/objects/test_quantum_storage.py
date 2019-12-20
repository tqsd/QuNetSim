import uuid
import sys

sys.path.append("../..")
from objects.quantum_storage import QuantumStorage

class FakeQubit(object):

    def __init__(self, id=None):
        if id is not None:
            self.id = id
        else:
            self.id = str(uuid.uuid4())


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


test_store_and_recover()
