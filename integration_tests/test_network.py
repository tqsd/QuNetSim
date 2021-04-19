import unittest

from qunetsim.components import Network, Host
from eqsn import EQSN


# @unittest.skip('')
class TestNetwork(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        EQSN.get_instance().stop_all()

    def setUp(self):
        Network.reset_network()

    def tearDown(self) -> None:
        pass

    def test_add_hosts(self):
        network = Network.get_instance()
        a = Host('A')
        b = Host('B')
        c = Host('C')

        network.add_hosts([a, b])
        self.assertEqual(network.num_hosts, 2)

        network.add_host(c)
        self.assertEqual(network.num_hosts, 3)
        network.stop(True)

    def test_remove_hosts(self):
        network = Network.get_instance()
        a = Host('A')
        b = Host('B')
        c = Host('C')

        network.add_hosts([a, b, c])
        self.assertEqual(network.num_hosts, 3)

        network.remove_host(a)
        self.assertEqual(network.num_hosts, 2)

        network.remove_host(b)
        self.assertEqual(network.num_hosts, 1)

        network.remove_host(c)
        self.assertEqual(network.num_hosts, 0)
        network.stop(True)

    def test_topology_star(self):
        network = Network.get_instance()

        network.generate_topology('star', 5)
        self.assertEqual(network.num_hosts, 5)
        self.assertEqual(network.classical_network.number_of_edges(), 8)

        network.stop(stop_hosts=True)

    def test_topology_linear(self):
        network = Network.get_instance()
        network.generate_topology('linear', 2)
        self.assertEqual(network.num_hosts, 2)
        self.assertEqual(network.classical_network.number_of_edges(), 2)

        network.stop(stop_hosts=True)

    def test_topology_complete(self):
        network = Network.get_instance()
        network.generate_topology('complete', 4)
        self.assertEqual(network.num_hosts, 4)
        self.assertEqual(network.classical_network.number_of_edges(), 4*3)

        network.stop(stop_hosts=True)

    def test_topology_not_implemented(self):
        network = Network.get_instance()
        with self.assertRaises(ValueError):
            network.generate_topology('unknown', 5)

        network.stop(stop_hosts=True)
