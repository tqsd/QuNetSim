import unittest
import numpy as np
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit

from qunetsim.backends import EQSNBackend
from qunetsim.backends import CQCBackend


# from qunetsim.backends import QuTipBackend

# @unittest.skip('')
class TestBackend(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        TestBackend.backends.append(EQSNBackend)
        # TestBackend.backends.append(CQCBackend)
        # TestBackend.backends.append(QuTipBackend)
        # TestBackend.backends.append(projectQ)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_qubit_initialization(self):
        backend = EQSNBackend()
        host_alice = Host('Alice', backend)
        qubit_initialized = Qubit(host_alice, theta=np.pi/2, phi=np.pi/2)

        self.assertAlmostEqual(host_alice.backend.eqsn.give_statevector_for(qubit_initialized.qubit)[1][0], 0.5-0.5j)
        self.assertAlmostEqual(host_alice.backend.eqsn.give_statevector_for(qubit_initialized.qubit)[1][1], 0.5+0.5j)

    # @unittest.skip('')
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
                self.assertEqual(q1.id, q2.id)
                self.assertEqual(backend.measure(q1, False),
                                 backend.measure(q2, False))

            network.stop(True)

    # @unittest.skip('')
    def test_single_gates(self):
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

            q = Qubit(alice)

            q.X()
            self.assertEqual(1, q.measure())

            q = Qubit(alice)

            q.H()
            q.H()
            self.assertEqual(0, q.measure())

            network.stop(True)

    @unittest.skip('')
    def test_density_operator_qutip(self):
        backend = QuTipBackend()
        network = Network.get_instance()
        network.start(["Alice", "Bob"], backend)
        alice = Host('Alice', backend)
        bob = Host('Bob', backend)
        alice.start()
        bob.start()
        network.add_host(alice)
        network.add_host(bob)

        q1 = backend.create_EPR(alice.host_id, bob.host_id)
        q2 = backend.receive_epr(
            bob.host_id, alice.host_id, q_id=q1.id)

        density_operator = backend.density_operator(q1)
        expected = np.diag([0.5, 0.5])
        self.assertTrue(np.allclose(density_operator, expected))

        # remove qubits
        backend.measure(q1, False)
        backend.measure(q2, False)

        network.stop(True)

    # @unittest.skip('')
    def test_density_operator(self):
        """
        Test EQSN.
        """
        backend = EQSNBackend()
        network = Network.get_instance()
        network.start(["Alice", "Bob"], backend)
        alice = Host('Alice', backend)
        bob = Host('Bob', backend)
        alice.start()
        bob.start()
        network.add_host(alice)
        network.add_host(bob)

        q1 = backend.create_EPR(alice.host_id, bob.host_id)
        q2 = backend.receive_epr(
            bob.host_id, alice.host_id, q_id=q1.id)

        density_operator = backend.density_operator(q1)
        expected = np.diag([0.5, 0.5])
        self.assertTrue(np.allclose(density_operator, expected))

        # remove qubits
        backend.measure(q1, False)
        backend.measure(q2, False)

        network.stop(True)

    # @unittest.skip('')
    def test_multiple_backends(self):
        for b in TestBackend.backends:
            backend1 = b()
            backend2 = b()
            network = Network.get_instance()
            network.start(["Alice", "Bob"], backend1)
            _ = Host('Alice', backend2)
            _ = Host('Bob', backend1)
            self.assertEqual(str(backend1._hosts), str(backend2._hosts))
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
