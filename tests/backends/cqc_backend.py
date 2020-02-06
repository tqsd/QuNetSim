import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
all_backends = [(CQCBackend, "Simulaqron")]

def test_adding_hosts_to_backend(backend_generator):
    print("Starrting adding a host test...")
    backend = backend_generator()
    network = Network.get_instance()
    network.start(["Alice"], backend)
    alice = Host('Alice', backend)
    alice.start()

    network.add_host(alice)
    network.stop(True)
    print("Test was successfull!")

def test_epr_generation(backend_generator):
    print("Starting EPR generation backend.")
    backend = backend_generator()
    network = Network.get_instance()
    network.start(["Alice", "Bob"], backend)
    alice = Host('Alice', backend)
    bob = Host('Bob', backend)
    alice.start()
    bob.start()
    network.add_host(alice)
    network.add_host(bob)

    # Test multiple times to eliminate probabilistic effects
    for _ in range(10):
        q1 = backend.create_EPR(alice.host_id, bob.host_id)
        q2 = backend.receive_epr(bob.host_id, q_id=q1.id)
        assert q1.id == q2.id
        assert backend.measure(q1) == backend.measure(q2)

    network.stop(True)
    print("Test was successful")

def test_qubit_with_backend(backend_generator):
    print("Starting backend qubit test...")
    # # TODO: Write test
    print("Test was successfull!")

def test_multiple_backends(backend_generator):
    print("Starting multiple backends test...")
    backend1 = backend_generator()
    backend2 = backend_generator()
    assert backend1._cqc_connections == backend2._cqc_connections
    network = Network.get_instance()
    network.start(["Alice", "Bob"], backend1)
    alice = Host('Alice', backend2)
    bob = Host('Bob', backend1)
    assert str(backend1._cqc_connections) == str(backend2._cqc_connections)
    assert str(backend1._hosts) == str(backend2._hosts)
    network.stop(True)
    print("Test was successfull!")

if __name__ == "__main__":
    for backend, name in all_backends:
        print("Starting tests for the %s backend..." % name)
        test_epr_generation(backend)
        test_adding_hosts_to_backend(backend)
        test_multiple_backends(backend)
        test_qubit_with_backend(backend)
        print("All tests were succefull!")
