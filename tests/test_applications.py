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


@unittest.skip('')
class TestOneHop(unittest.TestCase):
    sim_network = None
    network = None
    MAX_WAIT = 20

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ['Alice', 'Bob']
        cls.sim_network = SimulaNetwork(nodes=nodes, force=True)
        cls.sim_network.start()

        cls.network = Network.get_instance()
        cls.network.set_delay(0.7)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        if cls.sim_network is not None:
            cls.sim_network.stop()
        simulaqron_settings.default_settings()
        cls.network.stop()
        cls.network = None

        # os.system("simulaqron reset --force")

    def setUp(self):
        # time.sleep(2)
        pass

    def tearDown(self):
        for key in self.hosts.keys():
            self.hosts[key].cqc.flush()
            self.hosts[key].stop()
            self.network.remove_host(self.hosts[key])

    # @unittest.skip('')
    def test_one_hop_send_classical(self):
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

            q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
            i = 0
            while q2 is None and i < TestOneHop.MAX_WAIT:
                q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
                i += 1
                time.sleep(1)

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

            q_id = hosts['alice'].send_epr(hosts['bob'].host_id)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            self.assertIsNotNone(messages)
            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})

    # @unittest.skip('')
    def test_one_hop_superdense_epr_combination(self):
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
            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT and len(messages) == 0:
                messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            i = 0
            while q1 is None and i < TestOneHop.MAX_WAIT:
                q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
                i += 1
                time.sleep(1)

            self.assertIsNotNone(messages)
            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})

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
    def test_one_hop_teleport_superdense_combination(self):
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

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['bob'].host_id, q)

            messages = hosts['bob'].get_classical_messages()
            i = 0
            while i < TestOneHop.MAX_WAIT  and len(messages) == 0:
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
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)



#@unittest.skip('')
class TestTwoHop(unittest.TestCase):
    sim_network = None
    network = None
    hosts = None

    @classmethod
    def setUpClass(cls):
        # os.system("simulaqron start --nodes Alice,Bob,Eve --force")
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

    #@unittest.skip('')
    def test_send_classical(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts
            # A <-> B <-> E

            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')
            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_classical(hosts['eve'].host_id, 'hello')

            time.sleep(5)

            messages = hosts['eve'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': 'hello'})

    #@unittest.skip('')
    def test_epr(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts


            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            time.sleep(4)

            q_id = hosts['alice'].send_epr(hosts['eve'].host_id)
            time.sleep(10)

            q1 = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)

            time.sleep(5)

            q2 = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)

            Alice.flush()
            Bob.flush()
            Eve.flush()

            self.assertEqual(q1.measure(), q2.measure())

    #@unittest.skip('')
    def test_teleport(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['eve'].host_id, q)

            time.sleep(15)

            q2 = hosts['eve'].get_data_qubit(hosts['alice'].host_id)

            self.assertIsNotNone(q2)
            self.assertEqual(q2['q'].measure(), 1)

    #@unittest.skip('')
    def test_superdense(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['bob'].host_id, '01')

            time.sleep(3)

            messages = hosts['bob'].get_classical_messages()

            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': '01'})

    #@unittest.skip('')
    def test_classical_superdense_combination(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            hosts['alice'].send_superdense(hosts['eve'].host_id, '01')
            time.sleep(3)

            hosts['alice'].send_classical(hosts['eve'].host_id, 'hello')

            time.sleep(5)

            messages = hosts['eve'].get_classical_messages()
            i = 0

            while i < TestOneHop.MAX_WAIT and len(messages) < 2:
                messages = hosts['eve'].get_classical_messages()
                i += 1
                time.sleep(1)


            self.assertTrue(len(messages) > 0)
            self.assertEqual(messages[0], {'sender': hosts['alice'].host_id,
                                           'message': 'hello'})

            self.assertEqual(messages[1], {'sender': hosts['alice'].host_id,
                                           'message': '01'})


    #@unittest.skip('')
    def test_epr_teleport_combination(self):

        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection("Eve") as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}
            self.hosts = hosts
            time.sleep(5)

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            for h in hosts.values():
                self.network.add_host(h)

            time.sleep(10)

            q_id = hosts['alice'].send_epr(hosts['eve'].host_id)

            time.sleep(15)

            i = 0

            q1_epr = None
            q2_epr = None

            while (q1_epr is None or q2_epr is None) and i < TestOneHop.MAX_WAIT:

                if q1_epr is None:
                    q1_epr = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)

                if q2_epr is None:
                    q2_epr = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)

                time.sleep(1)
                i += 1

            self.assertEqual(q1_epr.measure(), q2_epr.measure())

            q = qubit(Alice)
            q.X()

            hosts['alice'].send_teleport(hosts['eve'].host_id, q)

            q_teleport = None

            i = 0

            while q_teleport is None and i < TestOneHop.MAX_WAIT * 2:
                q_teleport = hosts['eve'].get_data_qubit(hosts['alice'].host_id)
                time.sleep(1)
                i += 1


            self.assertIsNotNone(q_teleport)
            self.assertEqual(q_teleport['q'].measure(), 1)