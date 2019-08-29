import unittest
import time
import sys

from cqc.pythonLib import CQCConnection

sys.path.append("../..")
from components.host import Host
from components.network import Network


class TestApplications(unittest.TestCase):
    network = Network.get_instance()
    hosts = {}

    # def setUp(self):
    #     self.network.start()
    #     with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
    #             CQCConnection('Eve') as Eve:
    #         hosts = {'alice': Host('00000000', Alice),
    #                  'bob': Host('00000001', Bob),
    #                  'eve': Host('00000011', Eve)}
    #
    #         # A <-> B <-> E
    #         hosts['alice'].add_connection('00000001')
    #         hosts['bob'].add_connection('00000011')
    #
    #         hosts['alice'].start()
    #         hosts['bob'].start()
    #         hosts['eve'].start()
    #
    #         self.hosts = hosts
    #
    #         for h in hosts.values():
    #             self.network.add_host(h)
    #
    # def tearDown(self):
    #     print('stopping')
    #     for host in self.hosts.values():
    #         host.stop()
    #     self.network.stop()

    # def test_send_classical(self):
    #     self.hosts['alice'].send_classical(self.hosts['bob'].host_id, 'hello')
    #     self.assertTrue(True)

    def test_superdense(self):
        self.network.start()
        with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
                CQCConnection('Eve') as Eve:
            hosts = {'alice': Host('00000000', Alice),
                     'bob': Host('00000001', Bob),
                     'eve': Host('00000011', Eve)}

            # A <-> B <-> E
            hosts['alice'].add_connection('00000001')
            hosts['bob'].add_connection('00000011')

            hosts['alice'].start()
            hosts['bob'].start()
            hosts['eve'].start()

            self.hosts = hosts

            for h in hosts.values():
                self.network.add_host(h)

            q_id = self.hosts['alice'].send_epr(self.hosts['bob'].host_id)

            q1 = self.hosts['alice'].get_epr(self.hosts['bob'].host_id, q_id)
            print(q1)

            time.sleep(3)

            q2 = self.hosts['bob'].get_epr(self.hosts['alice'].host_id, q_id)
            self.assertEqual(q1.measure(), q2.measure())
