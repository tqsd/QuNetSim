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
from components import protocols


# @unittest.skip('')
class TestOneHop(unittest.TestCase):
    sim_network = None
    network = None
    hosts = None
    MAX_WAIT = 10

    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        nodes = ["Alice", "Bob"]
        topology = {"Alice": ["Bob"], "Bob": ["Alice"]}
        cls.sim_network = SimulaNetwork(nodes=nodes, topology=topology, force=True)
        cls.sim_network.start()

        cls.network = Network.get_instance()
        cls.network.start()
        if os.path.exists('./components/__pycache__'):
            os.system('rm -rf ./components/__pycache__/')

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
        # TODO: Why do tests fail on second attempt if we don't clear the cache?
        if os.path.exists('./tests/__pycache__'):
            os.system('rm -rf ./tests/__pycache__/')

    def tearDown(self):
        for key in self.hosts.keys():
            self.hosts[key].cqc.flush()
            self.hosts[key].stop()
            self.network.remove_host(self.hosts[key])
        self.network.set_drop_rate(0)

    # @unittest.skip('')
    def test_shares_epr(self):
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

            hosts['alice'].send_classical(hosts['bob'].host_id, 'Hello Bob')
            hosts['bob'].send_classical(hosts['alice'].host_id, 'Hello Alice')

            i = 0
            bob_messages = hosts['bob'].get_classical_messages()
            while i < TestOneHop.MAX_WAIT and len(bob_messages) == 0:
                bob_messages = hosts['bob'].get_classical_messages()
                i += 1
                time.sleep(1)

            i = 0
            alice_messages = hosts['alice'].get_classical_messages()
            while i < TestOneHop.MAX_WAIT and len(alice_messages) == 0:
                alice_messages = hosts['alice'].get_classical_messages()
                i += 1
                time.sleep(1)

            self.assertTrue(len(alice_messages) > 0)
            self.assertEqual(alice_messages[0]['sender'], hosts['bob'].host_id)
            self.assertEqual(alice_messages[0]['message'], 'Hello Alice')

            self.assertTrue(len(bob_messages) > 0)
            self.assertEqual(bob_messages[0]['sender'], hosts['alice'].host_id)
            self.assertEqual(bob_messages[0]['message'], 'Hello Bob')

    # @unittest.skip('')
    def test_await_ack(self):
        with CQCConnection("Bob") as Bob, CQCConnection("Alice") as Alice:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}

            self.hosts = hosts

            # A <-> B
            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            # print(f"ack test - SEND CLASSICAL - started at {time.strftime('%X')}")
            hosts['alice'].send_classical(hosts['bob'].host_id, 'hello bob one', await_ack=True)
            hosts['alice'].send_classical(hosts['bob'].host_id, 'hello bob two', await_ack=True)
            # print(f"ack test - SEND CLASSICAL - finished at {time.strftime('%X')}")

            saw_ack_1 = False
            saw_ack_2 = False
            messages = hosts['alice'].get_classical_messages()
            for m in messages:
                if m['message'] == protocols.ACK and m['sequence_number'] == 0:
                    saw_ack_1 = True
                if m['message'] == protocols.ACK and m['sequence_number'] == 1:
                    saw_ack_2 = True
                if saw_ack_1 and saw_ack_2:
                    break

            self.assertTrue(saw_ack_1)
            self.assertTrue(saw_ack_2)

            # print(f"ack test - SEND SUPERDENSE - started at {time.strftime('%X')}")
            hosts['alice'].send_superdense(hosts['bob'].host_id, '00', await_ack=True)
            # print(f"ack test - SEND SUPERDENSE - finished at {time.strftime('%X')}")

            saw_ack = False
            messages = hosts['alice'].get_classical_messages()
            for m in messages:
                if m['message'] == protocols.ACK and m['sequence_number'] == 2:
                    saw_ack = True
                    break

            self.assertTrue(saw_ack)

            # print(f"ack test - SEND TELEPORT - started at {time.strftime('%X')}")
            hosts['alice'].send_teleport(hosts['bob'].host_id, qubit(Alice), await_ack=True)
            # print(f"ack test - SEND TELEPORT - finished at {time.strftime('%X')}")

            saw_ack = False
            messages = hosts['alice'].get_classical_messages()
            for m in messages:
                if m['message'] == protocols.ACK and m['sequence_number'] == 3:
                    saw_ack = True
                    break

            self.assertTrue(saw_ack)

            # print(f"ack test - SEND EPR - started at {time.strftime('%X')}")
            hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)
            # print(f"ack test - SEND EPR - finished at {time.strftime('%X')}")

            saw_ack = False
            messages = hosts['alice'].get_classical_messages()
            for m in messages:
                if m['message'] == protocols.ACK and m['sequence_number'] == 4:
                    saw_ack = True
                    break

            self.assertTrue(saw_ack)

    #@unittest.skip('')
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

    #@unittest.skip('')
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

    #@unittest.skip('')
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

    #@unittest.skip('')
    def test_send_qubit_alice_to_bob(self):
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

    @unittest.skip('')
    def test_send_qubit_bob_to_alice(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:

            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}

            self.hosts = hosts

            # A <-> B
            hosts['bob'].add_connection('00000000')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            q = qubit(Bob)
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

    @unittest.skip('')
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

            # TODO: Superdense will consume the EPR pair generated in the first step so this test will fail

            q_id = hosts['alice'].send_epr(hosts['bob'].host_id)
            hosts['alice'].send_superdense(hosts['bob'].host_id, '01')

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

            i = 0
            q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
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

    #@unittest.skip('')
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

    #@unittest.skip('')
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
            self.assertTrue(len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)) == 1)

            i = 0
            while not hosts['bob'].shares_epr(hosts['alice'].host_id) and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            self.assertTrue(hosts['bob'].shares_epr(hosts['alice'].host_id))
            self.assertTrue(len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)) == 1)

            hosts['alice'].set_epr_memory_limit(2, hosts['bob'].host_id)
            hosts['bob'].set_epr_memory_limit(2)

            hosts['alice'].send_epr(hosts['bob'].host_id)
            hosts['alice'].send_epr(hosts['bob'].host_id)

            # Allow the network to process the requests
            time.sleep(1)

            self.assertTrue(len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)) == 2)

            i = 0
            while not hosts['bob'].shares_epr(hosts['alice'].host_id) and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            self.assertTrue(len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)) == 2)

    @unittest.skip('')
    def test_maximum_data_qubit_limit(self):
        with CQCConnection("Bob") as Bob, CQCConnection("Alice") as Alice:
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

            q_alice_id_1 = hosts['alice'].send_qubit(hosts['bob'].host_id, qubit(Alice))
            q_alice_id_2 = hosts['alice'].send_qubit(hosts['bob'].host_id, qubit(Alice))

            q_bob_id_1 = hosts['bob'].send_qubit(hosts['alice'].host_id, qubit(Bob))
            q_bob_id_2 = hosts['bob'].send_qubit(hosts['alice'].host_id, qubit(Bob))

            # Allow the network to process the requests
            # TODO: remove the need for this
            time.sleep(2)

            i = 0
            while len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 0 and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            i = 0
            while len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 0 and i < TestOneHop.MAX_WAIT:
                time.sleep(1)
                i += 1

            print(hosts['alice'].get_data_qubits(hosts['bob'].host_id))

            self.assertTrue(len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 1)
            self.assertTrue(hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_1).measure() == 0)
            self.assertIsNotNone(hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_2))
            self.assertTrue(len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 1)
            self.assertTrue(hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_1).measure() == 0)
            self.assertIsNotNone(hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_2))

            hosts['alice'].set_data_qubit_memory_limit(2, hosts['bob'].host_id)
            hosts['bob'].set_data_qubit_memory_limit(2)

            q_alice_id_1 = hosts['alice'].send_qubit(hosts['bob'].host_id, qubit(Alice))
            q_alice_id_2 = hosts['alice'].send_qubit(hosts['bob'].host_id, qubit(Alice))
            q_alice_id_3 = hosts['alice'].send_qubit(hosts['bob'].host_id, qubit(Alice))

            q_bob_id_1 = hosts['bob'].send_qubit(hosts['alice'].host_id, qubit(Bob))
            q_bob_id_2 = hosts['bob'].send_qubit(hosts['alice'].host_id, qubit(Bob))
            q_bob_id_3 = hosts['bob'].send_qubit(hosts['alice'].host_id, qubit(Bob))

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

            self.assertTrue(len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 2)
            self.assertTrue(hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_1).measure() == 0)
            self.assertTrue(hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_2).measure() == 0)
            self.assertIsNotNone(hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_3))

            self.assertTrue(len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 2)
            self.assertTrue(hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_1).measure() == 0)
            self.assertTrue(hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_2).measure() == 0)
            self.assertIsNotNone(hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_3))

    #@unittest.skip('')
    def test_packet_loss_classical(self):
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob)}
            self.network.set_drop_rate(0.5)
            self.hosts = hosts

            hosts['alice'].add_connection('00000001')

            hosts['alice'].start()
            hosts['bob'].start()

            for h in hosts.values():
                self.network.add_host(h)

            i=0
            while i < 50:
                hosts['alice'].send_classical(hosts['bob'].host_id, 'Hello Bob')
                i=i+1

            time.sleep(40)

            message_num = len(hosts['bob'].get_classical_messages())
            number_check = False

            if message_num > 15 and message_num < 35:
                number_check = True

            self.assertTrue(number_check)







