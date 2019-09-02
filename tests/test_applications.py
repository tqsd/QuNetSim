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

do_sequence = True


class TestOneHop(unittest.TestCase):
    sim_network = None
    network = None

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ['Alice', 'Bob', 'Eve']
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

    def setUp(self):
        pass

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

            time.sleep(2)

            messages = hosts['bob'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': 'hello'})

    # @unittest.skip('')
    def test_one_hop_epr(self):
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
            time.sleep(5)

            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)

            time.sleep(5)

            q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)

            self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_one_hop_teleport(self):
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

            time.sleep(2)

            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    # @unittest.skip('')
    def test_one_hop_superdense(self):
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

            time.sleep(3)

            messages = hosts['bob'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})


@unittest.skip('')
class TestTwoHop(unittest.TestCase):
    sim_network = None
    network = None

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ['Alice', 'Bob', 'Eve']
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

    def setUp(self):
        pass

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

            time.sleep(2)

            messages = hosts['bob'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': 'hello'})

    # @unittest.skip('')
    def test_one_hop_epr(self):
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
            time.sleep(5)

            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)

            time.sleep(5)

            q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)

            self.assertEqual(q1.measure(), q2.measure())

    # @unittest.skip('')
    def test_one_hop_teleport(self):
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

            time.sleep(2)

            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    # @unittest.skip('')
    def test_one_hop_superdense(self):
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

            time.sleep(3)

            messages = hosts['bob'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})
