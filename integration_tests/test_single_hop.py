from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit, Logger
from qunetsim.backends import EQSNBackend
import unittest
import time
import numpy as np

Logger.DISABLED = True

network = Network.get_instance()
hosts = {}


# @unittest.skip('')
class TestOneHop(unittest.TestCase):
    MAX_WAIT = 10

    @classmethod
    def setUpClass(cls):
        global network
        global hosts
        nodes = ["Alice", "Bob"]
        backend = EQSNBackend()
        network.start(nodes=nodes, backend=backend)
        hosts = {'alice': Host('Alice', backend),
                 'bob': Host('Bob', backend)}
        hosts['alice'].add_connection('Bob')
        hosts['bob'].add_connection('Alice')
        hosts['alice'].start()
        hosts['bob'].start()
        for h in hosts.values():
            network.add_host(h)

    @classmethod
    def tearDownClass(cls):
        global network
        global hosts
        network.stop(stop_hosts=True)

    def setUp(self):
        global network
        global hosts
        network.delay = 0.0
        network.packet_drop_rate = 0

        hosts['alice'].delay = 0.0
        hosts['bob'].delay = 0.0

        hosts['alice'].set_epr_memory_limit(-1)
        hosts['bob'].set_epr_memory_limit(-1)
        hosts['alice'].set_data_qubit_memory_limit(-1)
        hosts['bob'].set_data_qubit_memory_limit(-1)

    def tearDown(self):
        global hosts
        hosts['alice'].max_ack_wait = -1
        hosts['bob'].max_ack_wait = -1
        hosts['alice'].empty_classical()
        hosts['bob'].empty_classical()

    # @unittest.skip('')
    def test_shares_epr(self):
        q_id = hosts['alice'].send_epr(hosts['bob'].host_id)
        q1 = hosts['alice'].shares_epr(hosts['bob'].host_id)
        i = 0
        while not q1 and i < TestOneHop.MAX_WAIT:
            q1 = hosts['alice'].shares_epr(hosts['bob'].host_id)
            i += 1
            time.sleep(1)

        i = 0
        q2 = hosts['bob'].shares_epr(hosts['alice'].host_id)
        while not q2 and i < TestOneHop.MAX_WAIT:
            q2 = hosts['bob'].shares_epr(hosts['alice'].host_id)
            i += 1
            time.sleep(1)

        self.assertTrue(hosts['alice'].shares_epr(hosts['bob'].host_id))
        self.assertTrue(hosts['bob'].shares_epr(hosts['alice'].host_id))
        q_alice = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
        q_bob = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
        self.assertIsNotNone(q_alice)
        self.assertIsNotNone(q_bob)
        self.assertEqual(q_alice.measure(), q_bob.measure())
        self.assertFalse(hosts['alice'].shares_epr(hosts['bob'].host_id))
        self.assertFalse(hosts['bob'].shares_epr(hosts['alice'].host_id))

    # @unittest.skip('')
    def test_send_classical(self):
        hosts['alice'].send_classical(hosts['bob'].host_id, 'Hello Bob', await_ack=False)
        hosts['bob'].send_classical(hosts['alice'].host_id, 'Hello Alice', await_ack=False)
        i = 0
        bob_messages = hosts['bob'].classical

        while i < TestOneHop.MAX_WAIT and len(bob_messages) == 0:
            bob_messages = hosts['bob'].classical
            i += 1
            time.sleep(1)

        i = 0
        alice_messages = hosts['alice'].classical
        while i < TestOneHop.MAX_WAIT and len(alice_messages) == 0:
            alice_messages = hosts['alice'].classical
            i += 1
            time.sleep(1)

        self.assertTrue(len(alice_messages) > 0)
        self.assertEqual(alice_messages[0].sender, hosts['bob'].host_id)
        self.assertEqual(alice_messages[0].content, 'Hello Alice')

        self.assertTrue(len(bob_messages) > 0)
        self.assertEqual(bob_messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(bob_messages[0].content, 'Hello Bob')

    # @unittest.skip('')
    def test_send_classical_w_seq_number(self):
        hosts['alice'].reset_sequence_numbers()
        hosts['bob'].reset_sequence_numbers()

        hosts['alice'].send_classical(hosts['bob'].host_id, 'M0', await_ack=True)
        hosts['alice'].send_classical(hosts['bob'].host_id, 'M1', await_ack=True)
        hosts['alice'].send_classical(hosts['bob'].host_id, 'M2', await_ack=True)

        bob_messages = hosts['bob'].classical
        self.assertTrue(len(bob_messages) == 3)

        m0 = hosts['bob'].get_classical(hosts['alice'].host_id, seq_num=0)
        m1 = hosts['bob'].get_classical(hosts['alice'].host_id, seq_num=1)
        m2 = hosts['bob'].get_classical(hosts['alice'].host_id, seq_num=2)

        self.assertTrue(m0.seq_num == 0)
        self.assertTrue(m1.seq_num == 1)
        self.assertTrue(m2.seq_num == 2)

        self.assertTrue(m0.content == 'M0')
        self.assertTrue(m1.content == 'M1')
        self.assertTrue(m2.content == 'M2')

        hosts['bob'].empty_classical()
        self.assertTrue(len(hosts['bob'].classical) == 0)

    # @unittest.skip('')
    def test_max_wait_for_ack(self):
        global hosts
        ack_received_1 = hosts['alice'].send_classical(
            hosts['bob'].host_id, 'hello bob one', await_ack=True)
        hosts['alice'].max_ack_wait = 0
        ack_received_2 = hosts['alice'].send_classical(
            hosts['bob'].host_id, 'hello bob one', await_ack=True)
        self.assertTrue(ack_received_1)
        self.assertFalse(ack_received_2)

    # @unittest.skip('')
    def test_epr(self):
        global hosts

        q_id = hosts['alice'].send_epr(hosts['bob'].host_id)
        q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
        i = 0
        while q1 is None and i < TestOneHop.MAX_WAIT:
            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q1)
        i = 0
        q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
        while q2 is None and i < TestOneHop.MAX_WAIT:
            q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q2)
        assert q1 is not None
        assert q2 is not None
        self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_density_operator(self):
        global hosts

        q_id = hosts['alice'].send_epr(hosts['bob'].host_id)
        q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
        i = 0
        while q1 is None and i < TestOneHop.MAX_WAIT:
            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q1)
        i = 0
        q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
        while q2 is None and i < TestOneHop.MAX_WAIT:
            q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q2)
        assert q1 is not None
        assert q2 is not None

        # Density operator test
        density_operator1 = q1.density_operator()
        density_operator2 = q2.density_operator()
        expected_density_operator = np.diag([0.5, 0.5])

        self.assertTrue(np.allclose(density_operator1, expected_density_operator))
        self.assertTrue(np.allclose(density_operator2, expected_density_operator))

        # Check that the statevector has not changed
        self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_ghz(self):
        global hosts
        hosts['alice'].send_ghz([hosts['bob'].host_id], await_ack=True)

        q_alice = hosts['alice'].get_ghz(hosts['alice'].host_id)
        q_bob = hosts['bob'].get_ghz(hosts['alice'].host_id)

        self.assertIsNotNone(q_alice)
        self.assertIsNotNone(q_bob)
        self.assertEqual(q_alice.measure(), q_bob.measure())

    # @unittest.skip('')
    def test_qkd(self):
        global hosts
        key_size = 4
        ack = hosts['alice'].send_key(hosts['bob'].host_id, key_size)

        self.assertTrue(ack)
        key_alice, _ = hosts['alice'].get_key(hosts['bob'].host_id)
        key_bob, _ = hosts['bob'].get_key(hosts['alice'].host_id)

        self.assertEqual(key_alice, key_bob)

    # @unittest.skip('')
    def test_qkd_and_delete_loop(self):
        global hosts
        key_size = 4

        # delete, so that preexisting keys from other tests
        # do not interfer
        hosts['alice'].delete_key(hosts['bob'].host_id)
        hosts['bob'].delete_key(hosts['alice'].host_id)

        for _ in range(3):
            ack = hosts['alice'].send_key(hosts['bob'].host_id, key_size)

            self.assertTrue(ack)
            key_alice, _ = hosts['alice'].get_key(hosts['bob'].host_id)
            key_bob, _ = hosts['bob'].get_key(hosts['alice'].host_id)
            self.assertEqual(key_alice, key_bob)

            hosts['alice'].delete_key(hosts['bob'].host_id)
            hosts['bob'].delete_key(hosts['alice'].host_id)

            key_alice2 = hosts['alice'].get_key(hosts['bob'].host_id, 1)
            key_bob2 = hosts['bob'].get_key(hosts['alice'].host_id, 1)
            self.assertIsNone(key_alice2)
            self.assertIsNone(key_bob2)

    # @unittest.skip('')
    def test_teleport(self):
        global hosts

        q = Qubit(hosts['alice'])
        q.X()

        hosts['alice'].send_teleport(hosts['bob'].host_id, q)

        q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
        i = 0
        while q2 is None and i < TestOneHop.MAX_WAIT:
            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q2)
        assert q2 is not None
        self.assertEqual(q2.measure(), 1)

    # @unittest.skip('')
    def test_superdense(self):
        global hosts

        hosts['alice'].send_superdense(hosts['bob'].host_id, '01')

        messages = hosts['bob'].classical
        i = 0
        while i < TestOneHop.MAX_WAIT and len(messages) == 0:
            messages = hosts['bob'].classical
            i += 1
            time.sleep(1)

        self.assertIsNotNone(messages)
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, '01')

    # @unittest.skip('')
    def test_send_qubit_alice_to_bob(self):
        global hosts

        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_qubit(hosts['bob'].host_id, q)
        i = 0
        rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
        while i < TestOneHop.MAX_WAIT and rec_q is None:
            rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(rec_q)
        self.assertEqual(rec_q.measure(), 1)

    # @unittest.skip('')
    def test_send_qubit_bob_to_alice(self):
        global hosts

        q = Qubit(hosts['bob'])
        q.X()

        q_id = hosts['bob'].send_qubit(hosts['alice'].host_id, q)

        i = 0
        rec_q = hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_id)
        while i < TestOneHop.MAX_WAIT and rec_q is None:
            rec_q = hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(rec_q)
        self.assertEqual(rec_q.measure(), 1)

    # @unittest.skip('')
    def test_teleport_superdense_combination(self):
        global hosts

        hosts['alice'].send_superdense(hosts['bob'].host_id, '11')
        messages = hosts['bob'].classical
        i = 0
        while i < TestOneHop.MAX_WAIT and len(messages) == 0:
            messages = hosts['bob'].classical
            i += 1
            time.sleep(1)

        q = Qubit(hosts['alice'])
        q.X()

        hosts['alice'].send_teleport(hosts['bob'].host_id, q)
        q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
        i = 0
        while q2 is None and i < TestOneHop.MAX_WAIT:
            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(messages)
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, '11')

        self.assertIsNotNone(q2)
        assert q2 is not None
        self.assertEqual(q2.measure(), 1)

    @unittest.skip('')
    def test_maximum_epr_qubit_limit(self):
        global hosts

        hosts['alice'].set_epr_memory_limit(1)
        hosts['bob'].set_epr_memory_limit(1)
        hosts['alice'].max_ack_wait = 5
        hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)
        hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)

        self.assertTrue(hosts['alice'].shares_epr(hosts['bob'].host_id))
        self.assertTrue(
            len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)) == 1)
        self.assertTrue(hosts['bob'].shares_epr(hosts['alice'].host_id))
        self.assertTrue(
            len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)) == 1)

        hosts['alice'].set_epr_memory_limit(2, hosts['bob'].host_id)
        hosts['bob'].set_epr_memory_limit(2)

        hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)
        hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)

        self.assertTrue(
            len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)) == 2)
        self.assertTrue(
            len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)) == 2)

    @unittest.skip('')
    def test_maximum_data_qubit_limit(self):
        global hosts

        hosts['alice'].set_data_qubit_memory_limit(1)
        hosts['bob'].set_data_qubit_memory_limit(1)

        q_alice_id_1 = hosts['alice'].send_qubit(
            hosts['bob'].host_id, Qubit(hosts['alice']))
        time.sleep(2)
        q_alice_id_2 = hosts['alice'].send_qubit(
            hosts['bob'].host_id, Qubit(hosts['alice']))
        time.sleep(2)

        q_bob_id_1 = hosts['bob'].send_qubit(
            hosts['alice'].host_id, Qubit(hosts['bob']))
        time.sleep(2)
        q_bob_id_2 = hosts['bob'].send_qubit(
            hosts['alice'].host_id, Qubit(hosts['bob']))
        time.sleep(2)

        # Allow the network to process the requests
        # TODO: remove the need for this
        time.sleep(2)

        i = 0
        while len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) < 1 and i < TestOneHop.MAX_WAIT:
            time.sleep(1)
            i += 1

        i = 0
        while len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) < 1 and i < TestOneHop.MAX_WAIT:
            time.sleep(1)
            i += 1

        self.assertTrue(
            len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 1)
        self.assertTrue(hosts['alice'].get_data_qubit(
            hosts['bob'].host_id, q_bob_id_1).measure() == 0)
        self.assertIsNone(hosts['alice'].get_data_qubit(
            hosts['bob'].host_id, q_bob_id_2))
        self.assertTrue(
            len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 1)
        self.assertTrue(hosts['bob'].get_data_qubit(
            hosts['alice'].host_id, q_alice_id_1).measure() == 0)
        self.assertIsNone(hosts['bob'].get_data_qubit(
            hosts['alice'].host_id, q_alice_id_2))

        hosts['alice'].set_data_qubit_memory_limit(2, hosts['bob'].host_id)
        hosts['bob'].set_data_qubit_memory_limit(2)

        q_alice_id_1 = hosts['alice'].send_qubit(
            hosts['bob'].host_id, Qubit(hosts['alice']))
        time.sleep(2)
        q_alice_id_2 = hosts['alice'].send_qubit(
            hosts['bob'].host_id, Qubit(hosts['alice']))
        time.sleep(2)
        q_alice_id_3 = hosts['alice'].send_qubit(
            hosts['bob'].host_id, Qubit(hosts['alice']))
        time.sleep(2)

        q_bob_id_1 = hosts['bob'].send_qubit(
            hosts['alice'].host_id, Qubit(hosts['bob']))
        time.sleep(2)
        q_bob_id_2 = hosts['bob'].send_qubit(
            hosts['alice'].host_id, Qubit(hosts['bob']))
        time.sleep(2)
        q_bob_id_3 = hosts['bob'].send_qubit(
            hosts['alice'].host_id, Qubit(hosts['bob']))
        time.sleep(2)

        # Allow the network to process the requests
        time.sleep(3)

        i = 0
        while len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) < 2 and i < TestOneHop.MAX_WAIT:
            time.sleep(1)
            i += 1

        i = 0
        while len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) < 2 and i < TestOneHop.MAX_WAIT:
            time.sleep(1)
            i += 1

        self.assertTrue(
            len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 2)
        self.assertTrue(hosts['alice'].get_data_qubit(
            hosts['bob'].host_id, q_bob_id_1).measure() == 0)
        self.assertTrue(hosts['alice'].get_data_qubit(
            hosts['bob'].host_id, q_bob_id_2).measure() == 0)
        self.assertIsNone(hosts['alice'].get_data_qubit(
            hosts['bob'].host_id, q_bob_id_3))

        self.assertTrue(
            len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 2)
        self.assertTrue(hosts['bob'].get_data_qubit(
            hosts['alice'].host_id, q_alice_id_1).measure() == 0)
        self.assertTrue(hosts['bob'].get_data_qubit(
            hosts['alice'].host_id, q_alice_id_2).measure() == 0)
        self.assertIsNone(hosts['bob'].get_data_qubit(
            hosts['alice'].host_id, q_alice_id_3))

    # @unittest.skip('')
    def test_get_before_send(self):
        global hosts

        def alice_do(s):
            q = Qubit(hosts['alice'])
            q.X()
            time.sleep(1)
            _ = hosts['alice'].send_qubit(hosts['bob'].host_id, q)

        def bob_do(s):
            rec_q = hosts['bob'].get_data_qubit(
                hosts['alice'].host_id, wait=-1)
            self.assertIsNotNone(rec_q)
            self.assertEqual(rec_q.measure(), 1)

        t1 = hosts['bob'].run_protocol(bob_do)
        t2 = hosts['alice'].run_protocol(alice_do)

        t1.join()
        t2.join()
