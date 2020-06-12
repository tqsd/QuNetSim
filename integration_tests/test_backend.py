import unittest
from qunetsim.components.host import Host
from qunetsim.components.network import Network

from qunetsim.backends import EQSNBackend
from qunetsim.backends import CQCBackend


# @unittest.skip('')
class TestBackend(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        TestBackend.backends.append(EQSNBackend)
        TestBackend.backends.append(CQCBackend)
        # TestBackend.backends.append(projectQ)

    @classmethod
    def tearDownClass(cls):
        pass

    @unittest.skip('')
    def test_epr_generation(self):
        for b in TestBackend.backends:
            backend = b()
            network = Network.get_instance()
            network.start(["Alice", "Bob"], backend)
            alice = Host('Alice', backend)
            bob = Host('Bob', backend)
            alice.start()
            bob.start()
            network.add_host(alice)
            network.add_host(bob)

            # Test multiple times to eliminate probabilistic effects
            for _ in range(5):
                q1 = backend.create_EPR(alice.host_id, bob.host_id)
                q2 = backend.receive_epr(
                    bob.host_id, alice.host_id, q_id=q1.id)
                assert q1.id == q2.id
                assert backend.measure(q1, False) == backend.measure(q2, False)

            network.stop(True)

    @unittest.skip('')
    def test_multiple_backends(self):
        for b in TestBackend.backends:
            backend1 = b()
            backend2 = b()
            network = Network.get_instance()
            network.start(["Alice", "Bob"], backend1)
            _ = Host('Alice', backend2)
            _ = Host('Bob', backend1)
            assert str(backend1._hosts) == str(backend2._hosts)
            network.stop(True)

    @unittest.skip('')
    def test_adding_hosts_to_backend(self):
        for b in TestBackend.backends:
            backend = b()
            network = Network.get_instance()
            network.start(["Alice"], backend)
            alice = Host('Alice', backend)
            alice.start()

            network.add_host(alice)
            network.stop(True)
