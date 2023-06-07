import unittest
from qunetsim.components import Host, Network
from qunetsim.backends import EQSNBackend
import time

network = Network.get_instance()
hosts = {}

class TestGetClassicalAnyHost(unittest.TestCase):

    MAX_WAIT_TIME = 10

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

    def setUp(self) -> None:
        hosts['bob']._classical_messages.empty()
        hosts['alice']._classical_messages.empty()

    @classmethod
    def tearDownClass(cls):
        global network
        global hosts
        network.stop(stop_hosts=True)
    


    def test_get_all_with_wait_time(self):
        def listen_with_wait_time(s):
            time.sleep(2)
            msgs = hosts['bob'].get_classical_any_host(seq_num=None, wait=self.MAX_WAIT_TIME)
            self.assertEqual([x.content for x in msgs],['3','2','1'])

        def send_some_with_delay(s):
             hosts['alice'].send_classical(hosts['bob'].host_id,str(1),await_ack=True)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(2),await_ack=True)
             time.sleep(5)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(3),await_ack=True)

        t1 = hosts['bob'].run_protocol(listen_with_wait_time)
        t2 = hosts['alice'].run_protocol(send_some_with_delay)

        t1.join()
        t2.join()

    def test_get_seq_with_wait_time(self):
        def listen_with_wait_time(s):
            time.sleep(2)
            msg = hosts['bob'].get_classical_any_host(seq_num=2, wait=self.MAX_WAIT_TIME)
            self.assertEqual(msg.content,'3')

        def send_some_with_delay(s):
             hosts['alice'].send_classical(hosts['bob'].host_id,str(1),await_ack=True)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(2),await_ack=True)
             time.sleep(5)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(3),await_ack=True)

        t1 = hosts['bob'].run_protocol(listen_with_wait_time)
        t2 = hosts['alice'].run_protocol(send_some_with_delay)

        t1.join()
        t2.join()        

    def test_get_seq_with_wait_time_none_value(self):
        def listen_with_wait_time(s):
            time.sleep(2)
            msg = hosts['bob'].get_classical_any_host(seq_num=3, wait=self.MAX_WAIT_TIME) 
            self.assertEqual(msg,None)#seq_num not present

        def send_some_with_delay(s):
             hosts['alice'].send_classical(hosts['bob'].host_id,str(1),await_ack=True)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(2),await_ack=True)
             time.sleep(5)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(3),await_ack=True)

        t1 = hosts['bob'].run_protocol(listen_with_wait_time)
        t2 = hosts['alice'].run_protocol(send_some_with_delay)

        t1.join()
        t2.join() 
        
    def test_get_all_with_wait_time_empty_arr(self):
        def listen_with_wait_time(s):
            msgs = hosts['bob'].get_classical_any_host(None, wait=self.MAX_WAIT_TIME)
            self.assertEqual(msgs,[])

        def send_after_max_wait(s):
             time.sleep(self.MAX_WAIT_TIME+2)
             hosts['alice'].send_classical(hosts['bob'].host_id,str(1),await_ack=True)

        t1 = hosts['bob'].run_protocol(listen_with_wait_time)
        t2 = hosts['alice'].run_protocol(send_after_max_wait)

        t1.join()
        t2.join()

    def test_get_all_no_wait_time(self):
        # no msgs yet 
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, None)
        rec_msgs = hosts['bob'].get_classical_any_host(None, wait=0)
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, None)
        self.assertEqual(len(rec_msgs), 0)

        # with some msgs 
        for c in range(5):
            hosts['alice'].send_classical(hosts['bob'].host_id, str(c), await_ack=True)
        rec_msgs = hosts['bob'].get_classical_any_host(None, wait=0)
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, 'Alice')
        self.assertEqual(len(rec_msgs), 5)

    def test_get_seq_no_wait_time(self):
        # no msgs yet 
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, None)
        rec_msg = hosts['bob'].get_classical_any_host(0, wait=0)
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, None)
        self.assertEqual(rec_msg, None)

        # with some msgs 
        for c in range(5):
            hosts['alice'].send_classical(hosts['bob'].host_id, str(c), await_ack=True)
        rec_msg = hosts['bob'].get_classical_any_host(4, wait=0)
        self.assertEqual(hosts['bob']._classical_messages.last_msg_added_to_host, 'Alice')
        self.assertEqual(rec_msg.content, '4')

    def test_wait_data_type(self):
        self.assertRaises(Exception, hosts['bob'].get_classical_any_host, None, "1")


