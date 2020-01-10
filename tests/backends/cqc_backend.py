import sys

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from objects.qubit import Qubit
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
        q1, func = backend.create_EPR(alice.host_id, bob.host_id)
        q2 = func[0]()
        assert q1.id == q2.id
        assert q1.id == func[1]
        assert backend.measure(q1) == backend.measure(q2)

    network.stop(True)

def test_qubit_with_backend(backend_generator):
    print("Starting backend qubit test...")
    backend = backend_generator()

    print("Test was successfull!")




if __name__ == "__main__":
    for backend, name in all_backends:
        print("Starting tests for the %s backend..." % name)
        test_adding_hosts_to_backend(backend)
        test_epr_generation(backend)
        test_qubit_with_backend(backend)
        print("All tests were succefull!")
