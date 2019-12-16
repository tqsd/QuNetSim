import networkx as nx
import matplotlib.pyplot as plt
from queue import Queue
import time
import random
from components import protocols
from components.logger import Logger
from components.daemon_thread import DaemonThread
from inspect import signature
from objects.qubit import Qubit

from simulaqron.network import Network as SimulaNetwork
from simulaqron.settings import simulaqron_settings


# Network singleton
class Network:
    """ A network control singleton object. """
    __instance = None

    @staticmethod
    def get_instance():
        if Network.__instance is None:
            Network()
        return Network.__instance

    def __init__(self):
        if Network.__instance is None:
            self.ARP = {}
            # The directed graph for the connections
            self.classical_network = nx.DiGraph()
            self.sim_network = None
            self.quantum_network = nx.DiGraph()
            self._quantum_routing_algo = nx.shortest_path
            self._classical_routing_algo = nx.shortest_path
            self._use_hop_by_hop = True
            self._packet_queue = Queue()
            self._stop_thread = False
            self._queue_processor_thread = None
            self._delay = 0.5
            self._packet_drop_rate = 0
            self._x_error_rate = 0
            self._z_error_rate = 0
            Network.__instance = self
        else:
            raise Exception('this is a singleton class')

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
            raise Exception("The quantum routing algorithm must be a function.")

        num_algo_params = len(signature(algorithm).parameters)
        if num_algo_params != 3:
            raise Exception("The quantum routing algorithm function should take three parameters: " + \
                            "the (nx) graph representation of the network, the sender address and the receiver address.")

        self._quantum_routing_algo = algorithm

    def set_routing_algo(self, algorithm):
        """
        Set the routing algorithm for the network.

        Args:
             algorithm (function): The routing function. Should return a list of host_ids which represents the route
        """
        self._classical_routing_algo = algorithm

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

        Args:
             drop_rate (float): Probability of dropping a packet in the network
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
    def x_error_rate(self):
        """
        Get the X error rate of the network.
        Returns:
              The *x_error_rate* of the network.
        """

        return self._x_error_rate

    @x_error_rate.setter
    def x_error_rate(self, error_rate):
        """
        Set the X error rate of the network.

        Args:
             error_rate (float): Probability of a X error during a qubit transmission in the network
        """

        if error_rate < 0 or error_rate > 1:
            raise Exception('Error rate should be between 0 and 1.')

        if not (isinstance(error_rate, int) or isinstance(error_rate, float)):
            raise Exception('X error rate should be a number')

        self._x_error_rate = error_rate

    @property
    def z_error_rate(self):
        """
        Get the Z error rate of the network.

        Returns:
            (float): The Z error rate of the network.
        """
        return self._z_error_rate

    @z_error_rate.setter
    def z_error_rate(self, error_rate):
        """
        Set the Z error rate of the network.

        Args:
             error_rate (float): Probability of a Z error during a qubit transmission in the network
        """

        if error_rate < 0 or error_rate > 1:
            raise Exception('Error rate should be between 0 and 1.')

        if not (isinstance(error_rate, int) or isinstance(error_rate, float)):
            raise Exception('Z error rate should be a number')

        self._z_error_rate = error_rate

    def add_host(self, host):
        """
        Adds the *host* to ARP table and updates the network graph.

        Args:
            host (Host): The host to be added to the network.
        """

        Logger.get_instance().debug('host added: ' + host.host_id)
        self.ARP[host.host_id] = host
        self._update_network_graph(host)

    def remove_host(self, host):
        """
        Removes the host from the ARP table.

        Args:
            host (Host): The host to be removed from the network.
        """

        if host.host_id in self.ARP:
            del self.ARP[host.host_id]

    def _remove_network_node(self, host):
        """
        Removes the host from the ARP table.

        Args:
            host (Host): The host to be removed from the network.
        """

        try:
            self.classical_network.remove_node(host.host_id)
        except nx.NetworkXError:
            Logger.get_instance().error('attempted to remove a non-exiting node from network')

    def _update_network_graph(self, host):
        """
        Add host *host* to the network and update the graph representation of the network

        Args:
            host: The host to be added
        """
        self.classical_network.add_node(host.host_id)
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
             boolean: whether the sender and receiver share an EPR pair.
        """
        host_sender = self.get_host(sender)
        host_receiver = self.get_host(receiver)
        return host_sender.shares_epr(receiver) and host_receiver.shares_epr(sender)

    def get_host(self, host_id):
        """
        Returns the host with the *host_id*.

        Args:
            host_id (string): ID number of the host that is returned.

        Returns:
             Host: Host with the *host_id*
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
            host_id (string): ID number of the host whose name is returned if it is in ARP table

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
            source (string): ID of the source host
            dest (string) : ID of the destination host
        Returns:
            route (list): An ordered list of ID numbers on the shortest path from source to destination.
        """
        return self.quantum_routing_algo(self.quantum_network, source, dest)

    def get_classical_route(self, source, dest):
        """
        Gets the route for classical information from source to destination.

        Args:
            source (string): ID of the source host
            dest (string) : ID of the destination host

        Returns:
            route (list): An ordered list of ID numbers on the shortest path from source to destination.
        """
        return self.classical_routing_algo(self.classical_network, source, dest)

    def _entanglement_swap(self, sender, receiver, route, q_id, o_seq_num, blocked):
        """
        Performs a chain of entanglement swaps with the hosts between sender and receiver to create a shared EPR pair
        between sender and receiver.

        Args:
            sender (Host): Sender of the EPR pair
            receiver (Host): Receiver of the EPR pair
            route (list): Route between the sender and receiver
            q_id (string): Qubit ID of the sent EPR pair
            blocked (bool): If the pair being distributed is blocked or not
        """
        host_sender = self.get_host(sender)
        # TODO: Multiprocess this
        for i in range(len(route) - 1):
            if not self.shares_epr(route[i], route[i + 1]):
                self.get_host(route[i]).send_epr(route[i + 1], q_id, True)
            else:
                old_id = self.get_host(route[i]).change_epr_qubit_id(route[i + 1], q_id)
                self.get_host(route[i + 1]).change_epr_qubit_id(route[i], q_id, old_id)

        for i in range(len(route) - 2):
            host = self.get_host(route[i + 1])
            q = host.get_epr(route[0], q_id, wait=10)
            if q is None:
                Logger.get_instance().error('Entanglement swap failed')
                return
            data = {'q': q['q'],
                    'q_id': q_id,
                    'node': sender,
                    'o_seq_num': o_seq_num,
                    'type': protocols.EPR}

            if route[i + 2] == route[-1]:
                data = {'q': q['q'],
                        'q_id': q_id,
                        'node': sender,
                        'ack': True,
                        'o_seq_num': o_seq_num,
                        'type': protocols.EPR}

            host.send_teleport(route[i + 2], None, await_ack=True, payload=data, generate_epr_if_none=False)

        q2 = host_sender.get_epr(route[1], q_id=q_id)
        host_sender.add_epr(receiver, q2, q2.id, blocked)

    def _route_quantum_info(self, sender, receiver, qubits):
        """
        Routes qubits from sender to receiver.

        Args:
            sender (Host): Sender of qubits
            receiver (Host): Receiver qubits
            qubits (List of Qubits): The qubits to be sent
        """

        def transfer_qubits(s, r, store=False, original_sender=None):
            for q in qubits:
                Logger.get_instance().log('transfer qubits - sending qubit ' + q.id)

                x_err_var = random.random()
                z_err_var = random.random()
                if x_err_var > (1 - self.x_error_rate):
                    q.X()
                if z_err_var > (1 - self.z_error_rate):
                    q.Z()

                q.send_to(self.ARP[r])
                Logger.get_instance().log('transfer qubits - waiting to receive ' + q.id)
                q = self.ARP[r]._receive_qubit(q.id)
                Logger.get_instance().log('transfer qubits - received ' + q.id)

                # Update the set of qubits so that they aren't pointing at inactive qubits
                # qubits[index]['q'] = q.qubit

                # Unblock qubits in case they were blocked
                q.set_blocked_state(False)

                if store and original_sender is not None:
                    self.ARP[r].add_data_qubit(original_sender, q, q.id)

        route = self.get_quantum_route(sender, receiver)
        i = 0
        while i < len(route) - 1:
            Logger.get_instance().log('sending qubits from ' + route[i] + ' to ' + route[i + 1])

            if len(route[i:]) != 2:
                transfer_qubits(route[i], route[i + 1])
            else:
                transfer_qubits(route[i], route[i + 1], True, route[0])
            i += 1

    def _process_queue(self):
        """
        Runs a thread for processing the packets in the packet queue.
        """

        while True:
            if self._stop_thread:
                break

            if not self._packet_queue.empty():
                # To keep things from behaving well with simulaqron, we add a small
                # delay for packet queries
                time.sleep(self.delay)
                packet = self._packet_queue.get()

                # Simulate packet loss
                packet_drop_var = random.random()
                if packet_drop_var > (1 - self.packet_drop_rate):
                    Logger.get_instance().log("PACKET DROPPED")
                    continue

                sender, receiver = packet[protocols.SENDER], packet[protocols.RECEIVER]

                if packet['payload_type'] == protocols.QUANTUM:
                    self._route_quantum_info(sender, receiver, packet[protocols.PAYLOAD])

                try:
                    if self.use_hop_by_hop:
                        route = self.get_classical_route(sender, receiver)
                    elif packet['protocol'] == protocols.RELAY:
                        full_route = packet['route']
                        route = full_route[full_route.index(sender):]
                    else:
                        route = self.get_classical_route(sender, receiver)

                    if len(route) < 2:
                        raise Exception

                    elif len(route) == 2:
                        if packet['protocol'] != protocols.RELAY:
                            if packet['protocol'] == protocols.REC_EPR:
                                host_sender = self.get_host(sender)
                                receiver_name = self.get_host_name(receiver)
                                q = host_sender.cqc.createEPR(receiver_name)
                                q = Qubit(host_sender, qubit=q)
                                if packet['payload'] is not None:
                                    host_sender.add_epr(receiver, q, packet[protocols.PAYLOAD]['q_id'],
                                                        packet[protocols.PAYLOAD]['block'])
                                else:
                                    host_sender.add_epr(receiver, q)

                            self.ARP[receiver].rec_packet(packet)
                        else:
                            self.ARP[receiver].rec_packet(packet[protocols.PAYLOAD])
                    else:
                        if packet['protocol'] == protocols.REC_EPR:
                            q_id = packet['payload']['q_id']
                            blocked = packet['payload']['block']
                            q_route = self.get_quantum_route(sender, receiver)
                            DaemonThread(self._entanglement_swap,
                                         args=(sender, receiver, q_route, q_id,
                                               packet[protocols.SEQUENCE_NUMBER], blocked))
                        else:
                            network_packet = self._encode(route, packet)
                            self.ARP[route[1]].rec_packet(network_packet)

                except nx.NodeNotFound:
                    Logger.get_instance().error("route couldn't be calculated, node doesn't exist")
                except ValueError:
                    Logger.get_instance().error("route couldn't be calculated, value error")
                except Exception as e:
                    Logger.get_instance().error('Error in network: ' + str(e))

    def send(self, packet):
        """
        Puts the packet to the packet queue of the network.

        Args:
            packet (dict): Packet to be sent
        """

        self._packet_queue.put(packet)

    def stop(self, stop_hosts=False):
        """
        Stops the network.
        """

        Logger.get_instance().log("Network stopped")
        if stop_hosts:
            for host in self.ARP:
                self.ARP[host].stop(release_qubits=True)

        self._stop_thread = True
        if self.sim_network is not None:
            self.sim_network.stop()

    def start(self, nodes=None):
        """
        Starts the network.

        """
        if nodes is not None:
            simulaqron_settings.default_settings()
            self.sim_network = SimulaNetwork(nodes=nodes, force=True)
            self.sim_network.start()
        self._queue_processor_thread = DaemonThread(target=self._process_queue)

    def draw_network(self):
        """
        Draws a plot of the network.
        """

        nx.draw_networkx(self.classical_network, pos=nx.spring_layout(self.classical_network),
                         with_labels=True, hold=False)
        plt.show()

    def _encode(self, route, payload, ttl=10):
        """
        Adds another layer to the packet if route length between sender and receiver is greater than 2. Sets the
        protocol flag in this layer to RELAY and payload_type as SIGNAL and adds a variable
        Time-To-Live information in this layer.

        Args:
            route: route of the packet from sender to receiver
            payload (dict): Lower layers of the packet
            ttl(int): Time-to-Live parameter

        Returns:
            dict: Encoded RELAY packet
        """
        if payload[protocols.PROTOCOL] != protocols.RELAY:
            packet = {
                'sender': route[1],
                'payload': payload,
                'protocol': protocols.RELAY,
                'payload_type': protocols.SIGNAL,
                'TTL': ttl,
                'route': route
            }
        else:
            packet = payload
            packet['sender'] = route[1]

        if self.use_hop_by_hop:
            packet['receiver'] = route[-1]
        else:
            packet['receiver'] = route[2]

        return packet
