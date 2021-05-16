import unittest

from qunetsim.components import Network, Host
from eqsn import EQSN
from math import floor


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
        self.sample_list = [
            'A',
            'B',
            'C',
            'D',
            'E'
        ]

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

    def test_generate_topology_star(self):
        network = Network.get_instance()
        non_center_nodes = self.sample_list.copy()
        non_center_nodes.remove('A')

        network.generate_topology(self.sample_list, 'star')

        center_node = network.get_host('A')
        self.assertEqual(
            list(center_node.quantum_connections.keys()),
            non_center_nodes
        )
        self.assertEqual(
            list(center_node.classical_connections.keys()),
            non_center_nodes
        )

        for spoke in non_center_nodes:
            node = network.get_host(spoke)
            self.assertEqual(list(node.quantum_connections.keys()), ['A'])
            self.assertEqual(list(node.classical_connections.keys()), ['A'])

        network.stop(stop_hosts=True)

    def test_generate_topology_linear(self):
        network = Network.get_instance()
        network.generate_topology(self.sample_list, 'linear')

        # First Host
        host = network.get_host(self.sample_list[0])
        self.assertEqual(
            list(host.quantum_connections.keys()),
            [self.sample_list[1]]
        )
        # Last Host
        host = network.get_host(self.sample_list[-1])
        self.assertEqual(
            list(host.quantum_connections.keys()),
            [self.sample_list[-2]]
        )
        # Other Hosts
        for i in range(1, len(self.sample_list) - 2):
            host = network.get_host(self.sample_list[i])
            self.assertEqual(
                list(host.quantum_connections.keys()),
                [self.sample_list[i - 1], self.sample_list[i + 1]]
            )

        network.stop(stop_hosts=True)

    def test_generate_topology_ring(self):
        network = Network.get_instance()
        network.generate_topology(self.sample_list, 'ring')

        # First Host
        host = network.get_host(self.sample_list[0])
        self.assertEqual(
            list(host.quantum_connections.keys()),
            [self.sample_list[1], self.sample_list[-1]]
        )
        # Last Host
        host = network.get_host(self.sample_list[-1])
        self.assertEqual(
            list(host.quantum_connections.keys()),
            [self.sample_list[-2], self.sample_list[0]]
        )
        # Other Hosts
        for i in range(1, len(self.sample_list) - 2):
            host = network.get_host(self.sample_list[i])
            self.assertEqual(
                list(host.quantum_connections.keys()),
                [self.sample_list[i - 1], self.sample_list[i + 1]]
            )

        network.stop(stop_hosts=True)

    def test_generate_topology_mesh(self):
        network = Network.get_instance()
        network.generate_topology(self.sample_list, 'mesh')

        for host_name in self.sample_list:
            host = network.get_host(host_name)
            other_hosts = self.sample_list.copy()
            other_hosts.remove(host_name)
            self.assertEqual(
                list(host.quantum_connections.keys()),
                other_hosts
            )
            self.assertEqual(
                list(host.classical_connections.keys()),
                other_hosts
            )

        network.stop(stop_hosts=True)

    def test_generate_topology_tree(self):
        network = Network.get_instance()
        network.generate_topology(self.sample_list, 'tree')

        last_index = len(self.sample_list) - 1
        for i in range(last_index):
            host = network.get_host(self.sample_list[i])
            other_hosts = []
            if i != 0:
                other_hosts.append(self.sample_list[floor((i - 1) / 2)])
            if 2 * i + 1 <= last_index:
                other_hosts.append(self.sample_list[2 * i + 1])
            if 2 * i + 2 <= last_index:
                other_hosts.append(self.sample_list[2 * i + 2])
            self.assertEqual(
                list(host.quantum_connections.keys()),
                other_hosts
            )
            self.assertEqual(
                list(host.classical_connections.keys()),
                other_hosts
            )

        network.stop(stop_hosts=True)

    def test_generate_topology_not_implemented(self):
        network = Network.get_instance()
        with self.assertRaises(ValueError):
            network.generate_topology(self.sample_list, 'nonsense')

        network.stop(stop_hosts=True)
