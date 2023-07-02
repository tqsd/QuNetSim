import unittest
import numpy as np

from qunetsim.objects import Qubit
from qunetsim.components import Host
from random import randint
from qunetsim.components.network import Network
from qunetsim.objects.connections.channel_models import BitFlip, ClassicalModel, PhaseFlip, BinaryErasure, Fibre

# @unittest.skip('')
class TestHost(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_get_qubits_by_id(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host2 = Host('B')
        q4 = Qubit(host2)

        host.add_epr('B', q1)
        host.add_qubit('C', q2)
        host.add_ghz_qubit('D', q3)

        host2.add_qubit('A', q4)

        # Test all types of qubits
        self.assertEqual(q1, host.get_qubit_by_id(q1.id))
        self.assertEqual(q2, host.get_qubit_by_id(q2.id))
        self.assertEqual(q3, host.get_qubit_by_id(q3.id))

        # Test getting qubits from other hosts
        self.assertIsNone(host.get_qubit_by_id(q4.id))

        # Test getting qubits that don't exist
        self.assertIsNone(host.get_qubit_by_id('fake'))

    def test_get_data_qubit(self):
        with self.assertWarns(DeprecationWarning):
            host = Host('A')
            q1 = Qubit(host)

            host.add_qubit('A', q1)

            qs = host.get_data_qubit('A')
            self.assertIsInstance(qs, Qubit)

    def test_get_qubit(self):
        host = Host('A')
        q1 = Qubit(host)

        host.add_qubit('A', q1)

        qs = host.get_qubit('A')
        self.assertIsInstance(qs, Qubit)

    def test_get_data_qubits(self):
        with self.assertWarns(DeprecationWarning):
            host = Host('A')
            q1 = Qubit(host)
            q2 = Qubit(host)
            q3 = Qubit(host)

            host.add_qubit('B', q1)

            qs = host.get_data_qubits('B')
            self.assertEqual(len(qs), 1)

            host.add_qubit('B', q2)
            host.add_qubit('B', q3)

            qs = host.get_data_qubits('B')
            self.assertEqual(len(qs), 3)

            qs = host.get_data_qubits('B', remove_from_storage=True)
            self.assertEqual(len(qs), 3)

            qs = host.get_data_qubits('B', remove_from_storage=True)
            self.assertEqual(len(qs), 0)

    def test_get_qubits(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host.add_qubit('B', q1)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 1)

        host.add_qubit('B', q2)
        host.add_qubit('B', q3)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 3)

        qs = host.get_qubits('B', remove_from_storage=True)
        self.assertEqual(len(qs), 3)

        qs = host.get_qubits('B', remove_from_storage=True)
        self.assertEqual(len(qs), 0)

    def test_resetting_qubits(self):
        host = Host('A')
        q1 = Qubit(host)
        q2 = Qubit(host)
        q3 = Qubit(host)

        host.add_epr('B', q1)
        host.add_qubit('B', q2)
        host.add_ghz_qubit('B', q3)

        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 1)

        host.reset_data_qubits('B')
        qs = host.get_qubits('B')
        self.assertEqual(len(qs), 0)

    # @unittest.skip('')
    def test_connections(self):
        name = "A"
        neighbor = [str(x) for x in range(10)]
        a = Host(name)
        for x in neighbor:
            a.add_connection(x)

        connections = a.get_connections()
        for i in connections:
            self.assertTrue(i['connection'] in neighbor)
        a.backend.stop()

    # @unittest.skip('')
    def test_sequence_numbers(self):
        a = Host('A')
        neighbor = [str(x) for x in range(10)]
        random = [randint(0, 200) for _ in range(10)]
        for n, i in zip(neighbor, random):
            for _ in range(i):
                _ = a.get_next_sequence_number(n)

        for n, i in zip(neighbor, random):
            self.assertEqual(i, a.get_next_sequence_number(n))

        a.backend.stop()

    def test_add_connections(self):
        a = Host('A')

        a.add_connection('B')
        self.assertEqual(len(a.classical_connections), 1)
        self.assertEqual(len(a.quantum_connections), 1)

        a.add_c_connection('C')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 1)

        a.add_q_connection('D')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 2)

        a.add_connections(['E', 'F'])
        self.assertEqual(len(a.classical_connections), 4)
        self.assertEqual(len(a.quantum_connections), 4)

        a.add_c_connections(['G', 'H'])
        self.assertEqual(len(a.classical_connections), 6)
        self.assertEqual(len(a.quantum_connections), 4)

        a.add_q_connections(['I', 'J'])
        self.assertEqual(len(a.classical_connections), 6)
        self.assertEqual(len(a.quantum_connections), 6)

    def test_connection_models(self):
        a = Host('A')

        a.add_c_connection('B', ClassicalModel())
        self.assertEqual(a.classical_connections['B'].model.type, "Classical")
        with self.assertRaises(Exception):
            a.add_c_connection('C', BitFlip())
        self.assertEqual(len(a.classical_connections), 1)

        a.add_q_connection('D', BitFlip(0.5))
        self.assertEqual(a.quantum_connections['D'].model.type, "Quantum")
        a.add_q_connection('E', PhaseFlip(0.1))
        self.assertEqual(a.quantum_connections['E'].model.type, "Quantum")
        a.add_q_connection('F', BinaryErasure(0.2))
        self.assertEqual(a.quantum_connections['F'].model.type, "Quantum")
        a.add_q_connection('G', Fibre(alpha=0.3))
        self.assertEqual(a.quantum_connections['G'].model.type, "Quantum")

    def test_remove_connections(self):
        a = Host('A')
        a.add_connections(['B', 'C'])
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 2)
        a.remove_q_connection('B')
        self.assertEqual(len(a.classical_connections), 2)
        self.assertEqual(len(a.quantum_connections), 1)
        a.remove_c_connection('B')
        self.assertEqual(len(a.classical_connections), 1)
        self.assertEqual(len(a.quantum_connections), 1)
        a.remove_connection('C')
        self.assertEqual(len(a.classical_connections), 0)
        self.assertEqual(len(a.quantum_connections), 0)
        a.remove_connection('C')
        self.assertEqual(len(a.classical_connections), 0)
        self.assertEqual(len(a.quantum_connections), 0)

    def test_kwargs_runprotocol(self):
        def bob_do(host, sender):
            q = host.get_qubit(sender.host_id, wait=10)
            self.assertNotEqual(q, None)
            self.assertAlmostEqual(host.backend.eqsn.give_statevector_for(q.qubit)[1][0], 0.5-0.5j)

        def alice_do(host, receiver, theta, phi):
            q = Qubit(host)
            q.ry(theta)
            q.rz(phi)
            _, ack = host.send_qubit(receiver.host_id, q, await_ack=True)

        network = Network.get_instance()
        nodes = ['Alice', 'Bob']
        network.start(nodes)

        host_alice = Host('Alice')
        host_alice.add_connection('Bob')
        host_alice.start()

        host_bob = Host('Bob')
        host_bob.add_connection('Alice')
        host_bob.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.start()

        t1 = host_alice.run_protocol(alice_do, kwargs={'theta':np.pi/2, 'receiver':host_bob, 'phi':np.pi/2})
        t2 = host_bob.run_protocol(bob_do, kwargs={'sender':host_alice}, blocking=True)
        t1.join()

        s1 = host_alice.run_protocol(alice_do, (host_bob, np.pi/2, np.pi/2))
        s2 = host_bob.run_protocol(bob_do, (host_alice,), blocking=True)
        s1.join()

    def test_send_n_qubits(self):
        def sender_do(host, receiver, num_qubits, recv_ack=False):
            global q_id_list
            if recv_ack:
                q_id_list, ack_arr = host.send_qubits(receiver.host_id, host.make_list_n_qubits(num_qubits), await_ack=recv_ack)
                self.assertEqual(len(ack_arr), num_qubits)
            else:
                q_id_list = host.send_qubits(receiver.host_id, host.make_list_n_qubits(num_qubits), await_ack=recv_ack)
            self.assertEqual(len(q_id_list), num_qubits)

        def receiver_do(host, sender, num_qubits):
            global q_id_received
            q_id_received = []
            while len(q_id_received) < num_qubits:
                qubit_recv = host.get_qubit(sender.host_id, wait=10)
                if qubit_recv is not None:
                    q_id_received.append(qubit_recv.id)
            self.assertEqual(len(q_id_received), num_qubits)

        network = Network.get_instance()
        nodes = ['sender', 'receiver']
        network.start(nodes)

        host_sender = Host('sender')
        host_sender.add_connection('receiver')
        host_sender.start()

        host_receiver = Host('receiver')
        host_receiver.add_connection('sender')
        host_receiver.start()

        network.add_host(host_sender)
        network.add_host(host_receiver)
        network.start()

        host_sender.run_protocol(sender_do, kwargs={'num_qubits':5, 'receiver': host_receiver, 'recv_ack': True}, blocking=True)
        host_receiver.run_protocol(receiver_do, kwargs={'num_qubits':5, 'sender': host_sender}, blocking=True)

        network.stop(True)
        self.assertEqual(set(q_id_list), set(q_id_received))
        