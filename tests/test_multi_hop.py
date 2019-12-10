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


@unittest.skip('')
class TestTwoHop(unittest.TestCase):
    sim_network = None
    network = None
    hosts = None
    MAX_WAIT = 20

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ['Alice', 'Bob', 'Eve']
        cls.sim_network = SimulaNetwork(nodes=nodes, force=True)
        cls.sim_network.start()

        cls.network = Network.get_instance()
        cls.network.start()

        if os.path.exists('./components/__pycache__'):
            os.system('rm -rf ./components/__pycache__/')

    @classmethod
    def tearDownClass(cls):
        # if cls.sim_network is not None:
        #     cls.sim_network.stop()
        # simulaqron_settings.default_settings()
        #
        # cls.network.stop()
        # cls.network = None

        if cls.sim_network is not None:
            cls.sim_network.stop()
        simulaqron_settings.default_settings()
        cls.network.stop()
        cls.network = None
        if os.path.exists('./tests/__pycache__'):
            os.system('rm -rf ./tests/__pycache__/')

    def setUp(self):
        # TODO: Why do tests fail on second attempt if we don't clear the cache?
        if os.path.exists('./tests/__pycache__'):
            os.system('rm -rf ./tests/__pycache__/')

    def tearDown(self):
        for key in self.hosts.keys():
            self.hosts[key].cqc.flush()
            self.hosts[key].stop()
            self.network.remove_host(self.hosts[key])

    # OK
    #@unittest.skip('')
    def test_send_classical(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts
            # A <-> B <-> E

            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_classical(hosts['eve'].host_id, 'testing123')

            messages = hosts['eve'].classical
            i = 0
            while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['eve'].classical
                i += 1
                time.sleep(1)

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], 'testing123')

    # OK
    #@unittest.skip('')
    def test_full_network_routing(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts
            # A <-> B <-> E

            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            self.network.use_hop_by_hop = False
            hosts['alice'].send_classical(hosts['eve'].host_id, 'testing123')

            i = 0
            messages = hosts['eve'].classical
            while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['eve'].classical
                i += 1
                time.sleep(1)

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], 'testing123')

    # OK
    #@unittest.skip('')
    def test_epr(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts

            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q_id = hosts['alice'].send_epr(hosts['eve'].host_id)

            i = 0
            q1 = None
            q2 = None
            while i < TestTwoHop.MAX_WAIT and q1 is None:
                q1 = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q1)

            i = 0
            while i < TestTwoHop.MAX_WAIT and q2 is None:
                q2 = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q2)
            self.assertEqual(q1['q'].measure(), q2['q'].measure())

    #OK
    #@unittest.skip('')
    def test_teleport(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['eve'].host_id, q)
            q2 = None
            i = 0
            while i < TestTwoHop.MAX_WAIT and q2 is None:
                q2 = hosts['eve'].get_data_qubit(hosts['alice'].host_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    #OK
    #@unittest.skip('')
    def test_superdense(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['bob'].host_id, '10')

            messages = hosts['bob'].classical
            i = 0
            while i < TestTwoHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].classical
                i += 1
                time.sleep(1)

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], '10')

    # OK
    #@unittest.skip('')
    def test_classical_superdense_combination(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['eve'].host_id, '11')
            hosts['alice'].send_classical(hosts['eve'].host_id, 'hello')

            messages = hosts['eve'].classical
            i = 0
            while i < TestTwoHop.MAX_WAIT and len(messages) < 3:
                messages = hosts['eve'].classical
                i += 1
                time.sleep(1)

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[0]['message'], 'hello')
            self.assertEqual(messages[1]['sender'], hosts['alice'].host_id)
            self.assertEqual(messages[1]['message'], '11')

    # OK
    #@unittest.skip('')
    def test_epr_teleport_combination(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000000')

            hosts['bob'].add_connection('00000011')
            hosts['eve'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Alice)
            q.X()

            q_id = hosts['alice'].send_epr(hosts['eve'].host_id)

            # TODO: Why do we need this to pass the test?
            time.sleep(6)

            hosts['alice'].send_teleport(hosts['eve'].host_id, q)

            q1_epr = None
            q2_epr = None
            q_teleport = None

            i = 0
            while q1_epr is None and i < TestTwoHop.MAX_WAIT:
                q1_epr = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)
                if q1_epr is not None:
                    q1_epr = q1_epr['q']
                i += 1
                time.sleep(1)

            i = 0
            while q2_epr is None and i < TestTwoHop.MAX_WAIT:
                q2_epr = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)
                if q2_epr is not None:
                    q2_epr = q2_epr['q']
                i += 1
                time.sleep(1)

            i = 0
            while q_teleport is None and i < TestTwoHop.MAX_WAIT:
                q_teleport = hosts['eve'].get_data_qubit(hosts['alice'].host_id)
                if q_teleport is not None:
                    q_teleport = q_teleport['q']
                i += 1
                time.sleep(1)

            self.assertIsNotNone(q1_epr)
            self.assertIsNotNone(q2_epr)
            self.assertIsNotNone(q_teleport)
            self.assertEqual(q1_epr.measure(), q2_epr.measure())
            self.assertEqual(q_teleport.measure(), 1)
