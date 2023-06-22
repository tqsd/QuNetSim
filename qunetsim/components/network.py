import random
import time
from inspect import signature
from queue import Queue
from threading import Thread

import matplotlib.pyplot as plt
import networkx as nx

from qunetsim.backends import EQSNBackend
from qunetsim.objects import Qubit, RoutingPacket, Logger, DaemonThread
from qunetsim.objects.daemon_thread import is_thread_alive
from qunetsim.utils.constants import Constants


# Network singleton
class Network:
    """ A network control singleton object. """
    __instance = None

    @staticmethod
    def get_instance():
        if Network.__instance is None:
            Network()
        return Network.__instance

    @staticmethod
    def reset_network():
        if Network.__instance is not None:
            Network.__instance.stop(True)
            Network.__instance = None
        __instance = Network()

    def __init__(self):
        if Network.__instance is None:
            self.ARP = {}
            # The directed graph for the connections
            self.classical_network = nx.DiGraph()
            self.quantum_network = nx.DiGraph()
            self._quantum_routing_algo = nx.shortest_path
            self._classical_routing_algo = nx.shortest_path
            self._use_hop_by_hop = True
            self._packet_queues = {}
            self._use_ent_swap = False
            self._queue_processor_thread = None
            self._delay = 0.1
            self._packet_drop_rate = 0
            self._backend = None
            Network.__instance = self
        else:
            raise Exception('this is a singleton class')

    @property
    def use_ent_swap(self):
        return self._use_ent_swap

    @use_ent_swap.setter
    def use_ent_swap(self, use_ent_swap):
        self._use_ent_swap = use_ent_swap

    @property
    def use_hop_by_hop(self):
        """
        Get the routing style for the network.

        Returns:
            If the network uses hop by hop routing.
        """
        return self._use_hop_by_hop

    @use_hop_by_hop.setter
    def use_hop_by_hop(self, should_use):
        """
        Set the routing style for the network.
        Args:
            should_use (bool): If the network should use hop by hop routing or not
        """
        if not isinstance(should_use, bool):
            raise Exception('use_hop_by_hop should be a boolean value.')

        self._use_hop_by_hop = should_use

    @property
    def classical_routing_algo(self):
        """
        Get the routing algorithm for the network.
        """
        return self._classical_routing_algo

    @classical_routing_algo.setter
    def classical_routing_algo(self, algorithm):
        """
        Set the routing algorithm for the network.

        Args:
             algorithm (function): The routing function. Should return a list of host_ids which represents the route
        """
        self._classical_routing_algo = algorithm

    @property
    def quantum_routing_algo(self):
        """
        Gets the quantum routing algorithm of the network.

        Returns:
           algorithm (function): The quantum routing algorithm of the network
        """
        return self._quantum_routing_algo

    @quantum_routing_algo.setter
    def quantum_routing_algo(self, algorithm):
        """
        Sets the quantum routing algorithm of the network.

        Args:
            algorithm (function): The routing algorithm of the network. Should take an input and an output
        """
        if not callable(algorithm):
            raise Exception(
                "The quantum routing algorithm must be a function.")

        num_algo_params = len(signature(algorithm).parameters)
        if num_algo_params != 3:
            raise Exception(
                "The quantum routing algorithm function should take three parameters: " +
                "the (nx) graph representation of the network, the sender address and the " +
                "receiver address.")

        self._quantum_routing_algo = algorithm

    @property
    def delay(self):
        """
        Get the delay interval of the network.
        """
        return self._delay

    @delay.setter
    def delay(self, delay):
        """
        Set the delay interval of the network.

        Args:
             delay (float): Delay in network tick in seconds
        """
        if not (isinstance(delay, int) or isinstance(delay, float)):
            raise Exception('delay should be a number')

        if delay < 0:
            raise Exception('Delay should not be negative')

        self._delay = delay

    @property
    def packet_drop_rate(self):
        """
        Get the drop rate of the network.
        """
        return self._packet_drop_rate

    @packet_drop_rate.setter
    def packet_drop_rate(self, drop_rate):
        """
        Set the drop rate of the network.

        Args:
             drop_rate (float): Probability of dropping a packet in the network
        """

        if drop_rate < 0 or drop_rate > 1:
            raise Exception('Packet drop rate should be between 0 and 1')

        if not (isinstance(drop_rate, int) or isinstance(drop_rate, float)):
            raise Exception('Packet drop rate should be a number')

        self._packet_drop_rate = drop_rate

    @property
    def arp(self):
        return self.ARP

    def add_queue(self, host_id):
        self._packet_queues[host_id] = Queue()

    def remove_queue(self, host_id):
        del self._packet_queues[host_id]

    @property
    def num_hosts(self):
        return len(self.arp.keys())

    def add_host(self, host):
        """
        Adds the *host* to ARP table and updates the network graph.

        Args:
            host (Host): The host to be added to the network.
        """

        Logger.get_instance().debug('host added: ' + host.host_id)
        self.add_queue(host.host_id)
        self.ARP[host.host_id] = host
        self._update_network_graph(host)

    def add_hosts(self, hosts):
        """
        Adds the *hosts* to ARP table and updates the network graph.

        Args:
            hosts (list): The hosts to be added to the network.
        """
        for host in hosts:
            self.add_host(host)

    def remove_host(self, host):
        """
        Removes the host from the network.

        Args:
            host (Host): The host to be removed from the network.
        """

        if host.host_id in self.ARP:
            del self.ARP[host.host_id]
            self.remove_queue(host.host_id)
            if self.quantum_network.has_node(host.host_id):
                self.quantum_network.remove_node(host.host_id)
            if self.classical_network.has_node(host.host_id):
                self.classical_network.remove_node(host.host_id)

    def remove_c_connection(self, sender, receiver):
        if self.classical_network.has_edge(sender, receiver):
            self.classical_network.remove_edge(sender, receiver)

    def remove_q_connection(self, sender, receiver):
        if self.quantum_network.has_edge(sender, receiver):
            self.quantum_network.remove_edge(sender, receiver)

    def remove_hosts(self, hosts):
        for host in hosts:
            self.remove_host(host)

    def update_host(self, host):
        """
        Update the connections of a host in the network.
        Args:
            host:

        Returns:

        """
        self.remove_host(host)
        self.add_host(host)

    def _remove_network_node(self, host):
        """
        Removes the host from the ARP table.

        Args:
            host (Host): The host to be removed from the network.
        """

        try:
            self.classical_network.remove_node(host.host_id)
        except nx.NetworkXError:
            Logger.get_instance().error(
                'attempted to remove a non-exiting node from network')

    def _update_network_graph(self, host):
        """
        Add host *host* to the network and update the graph representation of the network

        Args:
            host: The host to be added
        """
        if not self.classical_network.has_node(host.host_id):
            self.classical_network.add_node(host.host_id)

        if not self.quantum_network.has_node(host.host_id):
            self.quantum_network.add_node(host.host_id)

        for connection in host.classical_connections:
            if not self.classical_network.has_edge(host.host_id, connection):
                edge = (host.host_id, connection, {'weight': 1})
                self.classical_network.add_edges_from([edge])

        for connection in host.quantum_connections:
            if not self.quantum_network.has_edge(host.host_id, connection):
                edge = (host.host_id, connection, {'weight': 1})
                self.quantum_network.add_edges_from([edge])

    def shares_epr(self, sender, receiver):
        """
        Returns boolean value dependent on if the sender and receiver share an EPR pair.

        Args:
            receiver (Host): The receiver
            sender (Host): The sender

        Returns:
             (bool) whether the sender and receiver share an EPR pair.
        """
        host_sender = self.get_host(sender)
        host_receiver = self.get_host(receiver)
        return host_sender.shares_epr(receiver) and host_receiver.shares_epr(
            sender)

    def get_host(self, host_id):
        """
        Returns the host with the *host_id*.

        Args:
            host_id (str): ID number of the host that is returned.

        Returns:
             Host (Host): Host with the *host_id*
        """
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id]

    def get_ARP(self):
        """
        Returns the ARP table.

        Returns:
             dict: The ARP table
        """
        return self.ARP

    def get_host_name(self, host_id):
        """
        Args:
            host_id (str): ID number of the host whose name is returned if it is in ARP table

        Returns the name of the host with *host_id* if the host is in ARP table , otherwise returns None.

        Returns:
             dict or None: Name of the host
        """
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id].cqc.name

    def get_quantum_route(self, source, dest):
        """
        Gets the route for quantum information from source to destination.

        Args:
            source (str): ID of the source host
            dest (str): ID of the destination host
        Returns:
            route (list): An ordered list of ID numbers on the shortest path from source to destination.
        """
        return self.quantum_routing_algo(self.quantum_network, source, dest)

    def get_classical_route(self, source, dest):
        """
        Gets the route for classical information from source to destination.

        Args:
            source (str): ID of the source host
            dest (str): ID of the destination host

        Returns:
            route (list): An ordered list of ID numbers on the shortest path from source to destination.
        """
        return self.classical_routing_algo(self.classical_network, source,
                                           dest)

    def _entanglement_swap(self, sender, receiver, route, q_id, o_seq_num,
                           blocked):
        """
        Performs a chain of entanglement swaps with the hosts between sender and receiver to create a shared EPR pair
        between sender and receiver.

        Args:
            sender (Host): Sender of the EPR pair
            receiver (Host): Receiver of the EPR pair
            route (list): Route between the sender and receiver
            q_id (str): Qubit ID of the sent EPR pair
            o_seq_num (int): The original sequence number
            blocked (bool): If the pair being distributed is blocked or not
        """
        host_sender = self.get_host(sender)

        def establish_epr(net, s, r):
            if not net.shares_epr(s, r):
                self.get_host(s).send_epr(r, q_id, await_ack=True)
            else:
                old_id = self.get_host(s).change_epr_qubit_id(r, q_id)
                net.get_host(r).change_epr_qubit_id(route[i], q_id, old_id)

        # Create EPR pairs on the route, where all EPR qubits have the id q_id
        threads = []
        for i in range(len(route) - 1):
            threads.append(DaemonThread(establish_epr,
                                        args=(self, route[i], route[i + 1])))

        for t in threads:
            t.join()

        for i in range(len(route) - 2):
            host = self.get_host(route[i + 1])
            q = host.get_epr(route[0], q_id, wait=10)
            if q is None:
                print("Host is %s" % host.host_id)
                print("Search host is %s" % route[0])
                print("Search id is %s" % q_id)
                print("EPR storage is")
                print(host.EPR_store)
                Logger.get_instance().error('Entanglement swap failed')
                return
            data = {'q': q,
                    'eq_id': q_id,
                    'node': sender,
                    'o_seq_num': o_seq_num,
                    'type': Constants.EPR}

            if route[i + 2] == route[-1]:
                data = {'q': q,
                        'eq_id': q_id,
                        'node': sender,
                        'ack': True,
                        'o_seq_num': o_seq_num,
                        'type': Constants.EPR}

            host.send_teleport(route[i + 2], None, await_ack=True,
                               payload=data, generate_epr_if_none=False)

        # Change in the storage that the EPR qubit is shared with the receiver
        q2 = host_sender.get_epr(route[1], q_id=q_id)
        host_sender.add_epr(receiver, q2, q_id, blocked)
        Logger.get_instance().log(
            'Entanglement swap was successful for pair with id '
            + q_id + ' between ' + sender + ' and ' + receiver)

    def _establish_epr(self, sender, receiver, q_id, o_seq_num, blocked):
        """
        Instead doing an entanglement swap, for efficiency we establish EPR pairs
        directly for simulation, if an entanglement swap would have been possible.

        Args:
            sender (Host): Sender of the EPR pair
            receiver (Host): Receiver of the EPR pair
            q_id (str): Qubit ID of the sent EPR pair
            o_seq_num (int): The original sequence number
            blocked (bool): If the pair being distributed is blocked or not
        """
        host_sender = self.get_host(sender)
        host_receiver = self.get_host(receiver)
        q1 = Qubit(host_sender)
        q2 = Qubit(host_sender)
        q1.H()
        q1.cnot(q2)
        host_sender.add_epr(receiver, q1, q_id, blocked)
        host_receiver.add_epr(sender, q2, q_id, blocked)
        host_receiver.send_ack(sender, o_seq_num)

    def _route_quantum_info(self, sender, receiver, qubits):
        """
        Routes qubits from sender to receiver.

        Args:
            sender (Host): Sender of qubits
            receiver (Host): Receiver qubits
            qubits (List of Qubits): The qubits to be sent
        """

        def transfer_qubits(r, s, original_sender=None):
            for q in qubits:
                # Modify the qubit according to error function of the model
                qubit_id = q.id
                q = self.ARP[s].quantum_connections[
                    self.ARP[r].host_id].model.qubit_func(q)

                if q is None:
                    # Log failure of transmission if qubit is lost
                    Logger.get_instance().log(
                        'transfer qubits - transfer of qubit ' + qubit_id + ' failed')
                    return False

                else:
                    Logger.get_instance().log(
                        'transfer qubits - sending qubit ' + q.id)

                    q.send_to(self.ARP[r].host_id)
                    Logger.get_instance().log(
                        'transfer qubits - received ' + q.id)

                    # Unblock qubits in case they were blocked
                    q.blocked = False

                    if self.ARP[r].q_relay_sniffing:
                        self.ARP[r].q_relay_sniffing_fn(original_sender,
                                                        receiver, q)
            return True

        route = self.get_quantum_route(sender, receiver)
        i = 0
        while i < len(route) - 1:
            Logger.get_instance().log(
                'sending qubits from ' + route[i] + ' to ' + route[i + 1])
            if not transfer_qubits(route[i + 1], route[i],
                                   original_sender=route[0]):
                return False
            i += 1
        return True

    def _process_queues(self):
        """
        Runs multiple threads for processing the packets in the packet queues.
        """

        def process_queue(packet_queue):
            """
            A single thread processes the packet in a single queue.
            Each host has it's own queue and thread for processing the queue.
            """
            packet = packet_queue.get()

            # If None packet is received, then stop thread
            if not packet.payload:
                return

            # Artificially delay the network
            if self.delay > 0:
                time.sleep(self.delay)

            # Simulate packet loss
            packet_drop_var = random.random()
            if packet_drop_var > (1 - self.packet_drop_rate):
                Logger.get_instance().log("PACKET DROPPED")
                if packet.payload_type == Constants.QUANTUM:
                    packet.payload.release()
                return

            sender, receiver = packet.sender, packet.receiver

            if packet.payload_type == Constants.QUANTUM:
                if not self._route_quantum_info(sender, receiver,
                                                [packet.payload]):
                    return

            try:
                if packet.protocol == Constants.RELAY and not self.use_hop_by_hop:
                    full_route = packet.route
                    route = full_route[full_route.index(sender):]
                else:
                    if packet.protocol == Constants.REC_EPR:
                        route = self.get_classical_route(sender, receiver)
                    else:
                        route = self.get_classical_route(sender, receiver)

                if len(route) < 2:
                    raise Exception('No route exists')

                elif len(route) == 2:
                    if packet.protocol != Constants.RELAY:
                        if packet.protocol == Constants.REC_EPR:
                            host_sender = self.get_host(sender)
                            q = host_sender \
                                .backend \
                                .create_EPR(host_sender.host_id,
                                            receiver,
                                            q_id=packet.payload['q_id'],
                                            block=packet.payload['blocked'])
                            host_sender.add_epr(receiver, q)
                        self.ARP[receiver].rec_packet(packet)
                    else:
                        self.ARP[receiver].rec_packet(packet.payload)
                else:
                    if packet.protocol == Constants.REC_EPR:
                        q_id = packet.payload['q_id']
                        blocked = packet.payload['blocked']
                        q_route = self.get_quantum_route(sender, receiver)

                        if self.use_ent_swap:
                            DaemonThread(self._entanglement_swap,
                                         args=(sender, receiver, q_route, q_id,
                                               packet.seq_num, blocked))
                        else:
                            DaemonThread(self._establish_epr,
                                         args=(sender, receiver, q_id,
                                               packet.seq_num, blocked))

                    else:
                        network_packet = self._encode(route, packet)
                        self.ARP[route[1]].rec_packet(network_packet)

            except nx.NodeNotFound:
                Logger.get_instance().error(
                    "route couldn't be calculated, node doesn't exist")
            except ValueError:
                Logger.get_instance().error(
                    "route couldn't be calculated, value error")
            except Exception as e:
                Logger.get_instance().error('Error in network: ' + str(e))

        while True:
            for host_name, queue in self._packet_queues.items():
                if not queue.empty() and not is_thread_alive(host_name):
                    thread = Thread(target=process_queue, args=[queue], daemon=False, name=host_name)
                    thread.start()

    def send(self, packet):
        """
        Puts the packet to the packet queue of the network.

        Args:
            packet (Packet): Packet to be sent
        """
        self._packet_queues.get(packet.sender).put(packet)

    def stop(self, stop_hosts=False):
        """
        Stops the network.
        """

        Logger.get_instance().log("Network stopped")
        try:
            if stop_hosts:
                for host in self.ARP:
                    self.ARP[host].stop(release_qubits=True)
                    # Send None to queue to stop the queue
                    self.send(RoutingPacket(sender=host, receiver=None, protocol=None, payload_type=None, payload=None,
                                            ttl=None, route=None))

            if self._backend is not None:
                self._backend.stop()
        except Exception as e:
            Logger.get_instance().error(e)

    def start(self, nodes=None, backend=None):
        """
        Starts the network.

        """
        if backend is None:
            self._backend = EQSNBackend()
        else:
            self._backend = backend
        if nodes is not None:
            self._backend.start(nodes=nodes)
        self._queue_processor_thread = DaemonThread(target=self._process_queues)

    def draw_classical_network(self):
        """
        Draws a plot of the network.
        """
        nx.draw_networkx(self.classical_network,
                         pos=nx.spring_layout(self.classical_network),
                         with_labels=True)
        plt.show()

    def draw_quantum_network(self):
        """
        Draws a plot of the network.
        """
        nx.draw_networkx(self.quantum_network,
                         pos=nx.spring_layout(self.quantum_network),
                         with_labels=True)
        plt.show()

    def _encode(self, route, payload, ttl=10):
        """
        Adds another layer to the packet if route length between sender and receiver is greater than 2. Sets the
        protocol flag in this layer to RELAY and payload_type as SIGNAL and adds a variable
        Time-To-Live information in this layer.

        Args:
            route: route of the packet from sender to receiver
            payload (Object): Lower layers of the packet
            ttl(int): Time-to-Live parameter

        Returns:
            RoutingPacket: Encoded RELAY packet
        """
        if payload.protocol != Constants.RELAY:
            packet = RoutingPacket(route[1], '', Constants.RELAY,
                                   Constants.SIGNAL,
                                   payload, ttl, route)
        else:
            packet = payload
            packet.sender = route[1]

        if self.use_hop_by_hop:
            packet.receiver = route[-1]
        else:
            packet.receiver = route[2]

        return packet

    @staticmethod
    def _get_star_topology_graph(hosts):
        return nx.star_graph(hosts)

    @staticmethod
    def _get_ring_topology_graph(hosts):
        graph = nx.path_graph(hosts)
        graph.add_edge(hosts[0], hosts[len(hosts) - 1])
        return graph

    @staticmethod
    def _get_mesh_topology_graph(hosts):
        return nx.complete_graph(hosts)

    @staticmethod
    def _get_linear_topology_graph(hosts):
        return nx.path_graph(hosts)

    @staticmethod
    def _get_tree_topology_graph(hosts):
        graph = nx.empty_graph(hosts)
        for i in range(0, len(hosts)):
            if 2 * i + 1 < len(hosts):
                graph.add_edge(hosts[i], hosts[2 * i + 1])
            if 2 * i + 2 < len(hosts):
                graph.add_edge(hosts[i], hosts[2 * i + 2])
        return graph

    topologies = {
        'mesh': lambda x: Network._get_mesh_topology_graph(x),
        'ring': lambda x: Network._get_ring_topology_graph(x),
        'star': lambda x: Network._get_star_topology_graph(x),
        'linear': lambda x: Network._get_linear_topology_graph(x),
        'tree': lambda x: Network._get_tree_topology_graph(x)
        # TODO: add bus topology
    }

    @staticmethod
    def _validate_topology_input(host_names, topology):
        if len(host_names) < 2:
            raise ValueError('insufficient hosts')
        if topology not in Network.topologies.keys():
            raise ValueError('topology not implemented')

    def _simple_topology_generation(self, host_names, topology, function):
        from qunetsim import Host

        Network._validate_topology_input(host_names, topology)

        graph = Network.topologies[topology](host_names)

        for host_name in host_names:
            if host_name not in self.ARP.keys():
                self.add_host(Host(host_name))

        for node, adj_list in graph.adjacency():
            h = self.get_host(node)
            function(h, adj_list.keys())
            self.add_host(h)
            h.start()

    def generate_topology(self, host_names: list, topology: str = 'mesh') \
            -> None:
        """
        Adjusts a network that already exists by adding both classic and
        quantum connections that fit the desired network topology. This method
        either adds new nodes or adds connections to existing hosts within
        the network.

        The supported network topologies are mesh, star, ring, linear, and
        tree.

        Args:
            host_names (list): The names for the new hosts.
            topology (str) {'mesh', 'star', 'ring', 'linear', 'tree'}: The
                network topology that will be created.
        """
        self.generate_c_topology(host_names, topology)
        self.generate_q_topology(host_names, topology)

    def generate_q_topology(self, host_names: list, topology: str = 'mesh') \
            -> None:
        """
        Adjusts a network that already exists by adding  quantum connections
        that fit the desired network topology. This method either adds new
        nodes or adds connections to existing hosts within the network.

        The supported network topologies are mesh, star, ring, linear, and
        tree.

        Args:
            host_names (list): The names for the new hosts.
            topology (str) {'mesh', 'star', 'ring', 'linear', 'tree'}: The
                network topology that will be created.
        """
        def add_quantum(x, y):
            return x.add_q_connections(y)
        self._simple_topology_generation(host_names, topology, add_quantum)

    def generate_c_topology(self, host_names: list, topology: str = 'mesh') \
            -> None:
        """
        Adjusts a network that already exists by adding  quantum connections
        that fit the desired network topology. This method either adds new
        nodes or adds connections to existing hosts within the network.

        The supported network topologies are mesh, star, ring, linear, and
        tree.

        Args:
            host_names (list): The names for the new hosts.
            topology (str) {'mesh', 'star', 'ring', 'linear', 'tree'}: The
                network topology that will be created.
        """
        def add_classic(x, y):
            return x.add_c_connections(y)
        self._simple_topology_generation(host_names, topology, add_classic)
