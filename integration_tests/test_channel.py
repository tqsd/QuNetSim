from qunetsim.objects import Qubit, Logger, Q_Connection, C_Connection, Binary_Erasure_Model, Fibre_Model
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.backends import EQSNBackend
from qunetsim.utils.constants import Constants
import unittest
import time

Logger.DISABLED = True

network = Network.get_instance()
hosts = {}

# unittest.skip('')
class TestChannel(unittest.TestCase):
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
        network.delay = 0.2
        network.packet_drop_rate = 0

        hosts['alice'].delay = 0.1
        hosts['bob'].delay = 0.1

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

    # unittest.skip('')
    def test_channel_BEC_success(self):
        global hosts

        hosts['alice'].quantum_connections[hosts['bob'].host_id].model = Binary_Erasure_Model(probability=0.0)
        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_qubit(hosts['bob'].host_id, q)
        i = 0
        rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
        while i < TestChannel.MAX_WAIT and rec_q is None:
            rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNotNone(rec_q)
        self.assertEqual(rec_q.measure(), 1)

    # unittest.skip('')
    def test_channel_BEC_failure(self):
        global hosts

        hosts['alice'].quantum_connections[hosts['bob'].host_id].model = Binary_Erasure_Model(probability=1.0)
        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_qubit(hosts['bob'].host_id, q)
        i = 0
        rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
        while i < TestChannel.MAX_WAIT and rec_q is None:
            rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertIsNone(rec_q)

    # unittest.skip('')
    def test_channel_Fibre_success(self):
        global hosts

        hosts['alice'].quantum_connections[hosts['bob'].host_id].model = Fibre_Model(length=0.0, alpha=0.0)
        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_qubit(hosts['bob'].host_id, q)
        i = 0
        rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
        while i < TestChannel.MAX_WAIT and rec_q is None:
            rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertEqual(hosts['alice'].quantum_connections[hosts['bob'].host_id].model.transmission_p, 1.0)
        self.assertIsNotNone(rec_q)
        self.assertEqual(rec_q.measure(), 1)

    # unittest.skip('')
    def test_channel_Fibre_failure(self):
        global hosts

        hosts['alice'].quantum_connections[hosts['bob'].host_id].model = Fibre_Model(length=10000000.0, alpha=1.0)
        q = Qubit(hosts['alice'])
        q.X()

        q_id = hosts['alice'].send_qubit(hosts['bob'].host_id, q)
        i = 0
        rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
        while i < TestChannel.MAX_WAIT and rec_q is None:
            rec_q = hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_id)
            i += 1
            time.sleep(1)

        self.assertEqual(hosts['alice'].quantum_connections[hosts['bob'].host_id].model.transmission_p, 0.0)
        self.assertIsNone(rec_q)