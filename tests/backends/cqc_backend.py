import sys

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from objects.qubit import Qubit
from components.network import Network

all_backends = [(CQCBackend, "Simulaqron")]

def test_adding_hosts_to_backend(backend):
    print("Starrting adding a host test...")
    backend = CQCBackend()
    network = Network.get_instance()
    network.start(["Alice"], backend)
    alice = Host('Alice', backend)
    alice.start()

    network.add_host(alice)
    network.stop(True)
    print("Test was successfull!")

def test_qubit_with_backend(backend):
    print("Starting backend qubit test...")
    backend = CQCBackend()

    print("Test was successfull!")




if __name__ == "__main__":
    for backend, name in all_backends:
        print("Starting tests for the %s backend..." % name)
        test_adding_hosts_to_backend(backend)
        test_qubit_with_backend(backend)
        print("All tests were succefull!")
