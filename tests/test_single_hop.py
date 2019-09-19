import unittest
import time
import sys
import os

from cqc.pythonLib import CQCConnection, qubit
from simulaqron.network import Network as SimulaNetwork
from simulaqron.settings import simulaqron_settings

sys.path.append("../..")
from components.host import Host
from components.network import Network


# @unittest.skip('')
class TestOneHop(unittest.TestCase):
    sim_network = None
    network = None
    hosts = None
    MAX_WAIT = 20

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ['Alice', 'Bob']
        cls.sim_network = SimulaNetwork(nodes=nodes, force=True)
        cls.sim_network.start()

        cls.network = Network.get_instance()
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        if cls.sim_network is not None:
            cls.sim_network.stop()
        simulaqron_settings.default_settings()
        cls.network.stop()
        cls.network = None

        if os.path.exists('./tests/__pycache__'):
            os.system('rm -rf ./tests/__pycache__/')

    def setUp(self):
        if os.path.exists('./tests/__pycache__'):
            os.system('rm -rf ./tests/__pycache__/')

    def tearDown(self):
        for key in self.hosts.keys():
            self.hosts[key].cqc.flush()
            self.hosts[key].stop()
            self.network.remove_host(self.hosts[key])

    # @unittest.skip('')
    def test_send_classical(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}

            self.hosts = hosts
            # A <-> B

            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_classical(hosts['bob'].host_id, 'hello')

            i = 0
            messages = hosts['bob'].get_classical_messages()
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], 'hello')

    # @unittest.skip('')
    def test_epr(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}

            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

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
            self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_teleport(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}

            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['bob'].host_id, q)

            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
            i = 0
            while q2 is None and i < TestOneHop.MAX_WAIT:
                q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    # @unittest.skip('')
    def test_superdense(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['bob'].host_id, '01')

            hosts['alice'].send_epr(hosts['bob'].host_id)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            self.assertIsNotNone(messages)
            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], '01')

    # @unittest.skip('')
    def test_send_qubit(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Alice)
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
    def test_superdense_epr_combination(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['bob'].host_id, '01')
            q_id = hosts['alice'].send_epr(hosts['bob'].host_id)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            i = 0
            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
            while q1 is None and i < TestOneHop.MAX_WAIT:
                q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(messages)
            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], '01')

            self.assertIsNotNone(q1)
            i = 0
            q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
            while q2 is None and i < TestOneHop.MAX_WAIT:
                q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q2)
            self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_teleport_superdense_combination(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['bob'].host_id, '11')

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['bob'].host_id, q)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
            i = 0
            while q2 is None and i < TestOneHop.MAX_WAIT:
                q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(messages)
            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], '11')

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    # @unittest.skip('')
    def test_maximum_epr_qubit_limit(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].set_memory_limit(1)
            hosts['bob'].set_memory_limit(1)

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_epr(hosts['bob'].host_id)
            hosts['alice'].send_epr(hosts['bob'].host_id)

            # Allow the network to process the requests
            time.sleep(1)

            self.assertTrue(hosts['alice'].shares_epr(hosts['bob'].host_id))
            self.assertTrue(len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)['qubits']) == 1)

            i = 0
            while not hosts['bob'].shares_epr(hosts['alice'].host_id) and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            self.assertTrue(hosts['bob'].shares_epr(hosts['alice'].host_id))
            self.assertTrue(len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)['qubits']) == 1)

            hosts['alice'].set_epr_memory_limit(2, hosts['bob'].host_id)
            hosts['bob'].set_epr_memory_limit(2)

            hosts['alice'].send_epr(hosts['bob'].host_id)
            hosts['alice'].send_epr(hosts['bob'].host_id)

            # Allow the network to process the requests
            time.sleep(1)

            self.assertTrue(len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)['qubits']) == 2)

            i = 0
            while not hosts['bob'].shares_epr(hosts['alice'].host_id) and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            self.assertTrue(len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)['qubits']) == 2)
