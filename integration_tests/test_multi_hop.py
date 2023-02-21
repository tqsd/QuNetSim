import unittest
import time

from qunetsim.backends import EQSNBackend
from qunetsim.components import Host, Network
from qunetsim.objects import Qubit

network = Network.get_instance()
hosts = {}


# @unittest.skip('')
class TestTwoHop(unittest.TestCase):
    sim_network = None
    network = None
    hosts = None
    MAX_WAIT = 20

    @classmethod
    def setUpClass(cls):
        global network
        global hosts
        nodes = ["Alice", "Bob", "Eve"]
        backend = EQSNBackend()
        network.start(nodes=nodes, backend=backend)
        hosts = {'alice': Host('Alice', backend),
                 'bob': Host('Bob', backend),
                 'eve': Host('Eve', backend)}
        hosts['alice'].add_connection('Bob')
        hosts['bob'].add_connection('Alice')
        hosts['bob'].add_connection('Eve')
        hosts['eve'].add_connection('Bob')
        hosts['alice'].start()
        hosts['bob'].start()
        hosts['eve'].start()

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
        network.use_hop_by_hop = True

        hosts['alice'].delay = 0.0
        hosts['bob'].delay = 0.0
        hosts['eve'].delay = 0.0

        hosts['alice'].set_epr_memory_limit(-1)
        hosts['bob'].set_epr_memory_limit(-1)
        hosts['eve'].set_epr_memory_limit(-1)

        hosts['alice'].set_data_qubit_memory_limit(-1)
        hosts['bob'].set_data_qubit_memory_limit(-1)
        hosts['eve'].set_data_qubit_memory_limit(-1)

    def tearDown(self):
        hosts['alice'].max_ack_wait = -1
        hosts['bob'].max_ack_wait = -1
        hosts['eve'].max_ack_wait = -1
        hosts['alice'].empty_classical()
        hosts['bob'].empty_classical()
        hosts['eve'].empty_classical()

    # @unittest.skip('')
    def test_send_classical(self):
        hosts['alice'].send_classical(hosts['eve'].host_id, 'testing123')

        messages = hosts['eve'].classical
        i = 0
        while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
            messages = hosts['eve'].classical
            i += 1
            time.sleep(1)

        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, 'testing123')

    # @unittest.skip('')
    def test_send_classical_w_seq_number(self):
        hosts['alice'].reset_sequence_numbers()
        hosts['bob'].reset_sequence_numbers()
        hosts['eve'].reset_sequence_numbers()

        hosts['alice'].send_classical(hosts['eve'].host_id, 'M0', await_ack=True)
        hosts['alice'].send_classical(hosts['eve'].host_id, 'M1', await_ack=True)
        hosts['alice'].send_classical(hosts['eve'].host_id, 'M2', await_ack=True)

        eve_messages = hosts['eve'].classical
        self.assertTrue(len(eve_messages) == 3)

        m0 = hosts['eve'].get_classical(hosts['alice'].host_id, seq_num=0)
        m1 = hosts['eve'].get_classical(hosts['alice'].host_id, seq_num=1)
        m2 = hosts['eve'].get_classical(hosts['alice'].host_id, seq_num=2)

        self.assertTrue(m0.seq_num == 0)
        self.assertTrue(m1.seq_num == 1)
        self.assertTrue(m2.seq_num == 2)

        self.assertTrue(m0.content == 'M0')
        self.assertTrue(m1.content == 'M1')
        self.assertTrue(m2.content == 'M2')

        hosts['eve'].empty_classical()
        self.assertTrue(len(hosts['eve'].classical) == 0)

    # @unittest.skip('')
    def test_full_network_routing(self):
        network.use_hop_by_hop = False
        hosts['alice'].send_classical(hosts['eve'].host_id, 'testing123')

        i = 0
        messages = hosts['eve'].classical
        while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
            messages = hosts['eve'].classical
            i += 1
            time.sleep(1)

        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, 'testing123')

    # @unittest.skip('')
    def test_epr(self):
        q_id = hosts['alice'].send_epr(hosts['eve'].host_id)

        q1 = None
        q2 = None

        q1 = hosts['alice'].get_epr(hosts['eve'].host_id, q_id, wait=TestTwoHop.MAX_WAIT)

        self.assertIsNotNone(q1)

        q2 = hosts['eve'].get_epr(hosts['alice'].host_id, q_id, wait=TestTwoHop.MAX_WAIT)

        self.assertIsNotNone(q2)
        self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_teleport(self):
        q = Qubit(hosts['alice'])
        q.X()

        hosts['alice'].send_teleport(hosts['eve'].host_id, q)
        q2 = None
        i = 0
        while i < TestTwoHop.MAX_WAIT and q2 is None:
            q2 = hosts['eve'].get_qubit(hosts['alice'].host_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(q2)
        self.assertEqual(q2.measure(), 1)

    # @unittest.skip('')
    def test_superdense(self):
        hosts['alice'].send_superdense(hosts['bob'].host_id, '10')

        messages = hosts['bob'].classical
        i = 0
        while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
            messages = hosts['bob'].classical
            i += 1
            time.sleep(1)

        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, '10')

    # @unittest.skip('')
    def test_classical_superdense_combination(self):
        hosts['alice'].send_superdense(hosts['eve'].host_id, '11')
        hosts['alice'].send_classical(hosts['eve'].host_id, 'hello')

        messages = hosts['eve'].classical
        i = 0.0
        while i < TestTwoHop.MAX_WAIT and len(messages) < 3:
            messages = hosts['eve'].classical
            i += 1
            time.sleep(1)

        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].sender, hosts['alice'].host_id)
        self.assertEqual(messages[0].content, 'hello')
        self.assertEqual(messages[1].sender, hosts['alice'].host_id)
        self.assertEqual(messages[1].content, '11')

    # @unittest.skip('')
    def test_epr_teleport_combination(self):
        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_epr(hosts['eve'].host_id)
        hosts['alice'].send_teleport(hosts['eve'].host_id, q)

        q1_epr = None
        q2_epr = None
        q_teleport = None

        q1_epr = hosts['alice'].get_epr(hosts['eve'].host_id, q_id, wait=TestTwoHop.MAX_WAIT)

        q2_epr = hosts['eve'].get_epr(hosts['alice'].host_id, q_id, wait=TestTwoHop.MAX_WAIT)

        q_teleport = hosts['eve'].get_qubit(hosts['alice'].host_id, wait=TestTwoHop.MAX_WAIT)

        self.assertIsNotNone(q1_epr)
        self.assertIsNotNone(q2_epr)
        self.assertIsNotNone(q_teleport)
        self.assertEqual(q1_epr.measure(), q2_epr.measure())
        self.assertEqual(q_teleport.measure(), 1)

    # @unittest.skip('')
    def test_get_before_send(self):
        def eve_do(eve):
            q = hosts['eve'].get_qubit(hosts['alice'].host_id, wait=10)
            self.assertNotEqual(q, None)

        def alice_do(alice):
            time.sleep(1)
            q = Qubit(hosts['alice'])
            _ = hosts['alice'].send_qubit(hosts['eve'].host_id, q)

        t1 = hosts['eve'].run_protocol(eve_do)
        t2 = hosts['alice'].run_protocol(alice_do)

        t1.join()
        t2.join()

    # @unittest.skip('')
    def test_qkd_and_delete(self):
        global hosts
        key_size = 4

        ack = hosts['alice'].send_key(hosts['eve'].host_id, key_size)
        self.assertTrue(ack)

        key_alice, _ = hosts['alice'].get_key(hosts['eve'].host_id)
        key_bob, _ = hosts['eve'].get_key(hosts['alice'].host_id)
        self.assertEqual(key_alice, key_bob)
        hosts['alice'].delete_key(hosts['eve'].host_id)
        hosts['eve'].delete_key(hosts['alice'].host_id)

        key_alice = hosts['alice'].get_key(hosts['eve'].host_id, 1)
        key_bob = hosts['eve'].get_key(hosts['alice'].host_id, 1)

        self.assertIsNone(key_alice, "key was not delted")
        self.assertIsNone(key_bob, "key was not delted")
