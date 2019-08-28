import networkx as nx
import matplotlib.pyplot as plt
from queue import Queue
import time
from components import protocols
from components.logger import Logger
import threading


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


# Network singleton
class Network:
    __instance = None

    @staticmethod
    def get_instance():
        if Network.__instance is None:
            Network()
        return Network.__instance

    def __init__(self):
        if Network.__instance is None:
            self.ARP = {}
            self.network = nx.DiGraph()
            self.routing_algo = nx.shortest_path
            self._packet_queue = Queue()
            self._stop_thread = False
            self._queue_processor_thread = None
            self.delay = 0.5
            Network.__instance = self
        else:
            raise Exception('this is a singleton class')

    def set_routing_algo(self, algo):
        self.routing_algo = algo

    def set_delay(self, delay):
        self.delay = delay

    def add_host(self, host):
        Logger.get_instance().debug('host added: ' + host.host_id)
        self.ARP[host.host_id] = host
        self._update_network_graph(host)

    def _update_network_graph(self, host):
        self.network.add_node(host.host_id)

        for connection in host.connections:
            if not self.network.has_edge(host.host_id, connection):
                edge = (host.host_id, connection, {'weight': 1})
                self.network.add_edges_from([edge])

            if not self.network.has_edge(connection, host.host_id):
                edge = (connection, host.host_id, {'weight': 1})
                self.network.add_edges_from([edge])

    def shares_epr(self, sender, receiver):
        host_sender = self.get_host(sender)
        host_receiver = self.get_host(receiver)

        return host_sender.shares_epr(receiver) and host_receiver.shares_epr(sender)

    def get_host(self, host_id):
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id]

    def get_host_name(self, host_id):
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id].cqc.name

    def get_route(self, source, dest):
        return self.routing_algo(self.network, source=source, target=dest)

    def _send_network_packet(self, src, dest, link_layer_packet):
        network_packet = protocols.encode(src, dest, protocols.RELAY, link_layer_packet, protocols.SIGNAL)
        self.ARP[dest].rec_packet(network_packet)

        return None

    def encode(self, sender, receiver, payload, ttl=10):
        packet = {
            'sender': sender,
            'receiver': receiver,
            'payload': payload,
            'protocol': protocols.RELAY,
            'payload_type': protocols.SIGNAL,
            'TTL': ttl
        }
        return packet

    def route_quantum_info(self, sender, receiver, qubits):
        def transfer_qubits(s, r, store=False, original_sender=None):
            for index, q in enumerate(qubits):
                Logger.get_instance().log('transfer qubits - sending qubit ' + qubits[index]['q_id'])
                self.ARP[s].cqc.sendQubit(q['q'], self.get_host_name(r))
                Logger.get_instance().log('transfer qubits - waiting to receive ' + qubits[index]['q_id'])
                q = self.ARP[r].cqc.recvQubit()
                Logger.get_instance().log('transfer qubits - received ' + qubits[index]['q_id'])

                # Update the set of qubits so that they aren't pointing at inactive qubits
                qubits[index]['q'] = q

                # Unblock qubits incase they were blocked
                qubits[index]['blocked'] = False

                if store and original_sender is not None:
                    self.ARP[r].add_data_qubit(original_sender, qubits[index]['q'], qubits[index]['q_id'])

        route = self.get_route(sender, receiver)
        i = 0
        while i < len(route) - 1:
            Logger.get_instance().log('sending qubits from ' + route[i] + ' to ' + route[i + 1])

            if len(route[i:]) != 2:
                transfer_qubits(route[i], route[i + 1])
            else:
                transfer_qubits(route[i], route[i + 1], True, route[0])

            i += 1

    def send(self, packet):
        self._packet_queue.put(packet)

    def _process_queue(self):
        while True:
            if self._stop_thread:
                break

            if not self._packet_queue.empty():
                # To keep things from behaving well with simulaqron, we add a small
                # delay for packet queries
                time.sleep(self.delay)

                packet = self._packet_queue.get()
                sender, receiver = packet['sender'], packet['receiver']

                if packet['payload_type'] == protocols.QUANTUM:
                    self.route_quantum_info(sender, receiver, packet['payload'])

                try:
                    # TODO: what to do if route doesn't exist?
                    route = self.get_route(sender, receiver)

                    if len(route) < 2:
                        raise Exception

                    elif len(route) == 2:
                        if packet['protocol'] != protocols.SEND_TELEPORT:
                            Logger.get_instance().log('sending packet from ' + sender + ' to ' + receiver)
                        if packet['protocol'] != protocols.RELAY:
                            self.ARP[receiver].rec_packet(packet)
                        else:
                            self.ARP[receiver].rec_packet(packet['payload'])

                    else:
                        if packet['protocol'] != protocols.SEND_TELEPORT:
                            Logger.get_instance().log('sending packet from ' + route[0] + ' to ' + route[1])
                        # Here we're using hop by hop approach
                        if packet['protocol'] != protocols.RELAY:
                            network_packet = self.encode(route[0], route[1], packet)
                        else:
                            packet['receiver'] = route[1]
                            network_packet = packet
                        self.ARP[route[1]].rec_packet(network_packet)

                except nx.NodeNotFound:
                    Logger.get_instance().error("route couldn't be calculated, node doesn't exist")
                    return

                except ValueError:
                    Logger.get_instance().error("route couldn't be calculated, value error")
                    return

    def stop(self):
        Logger.get_instance().log("Network stopped")
        self._stop_thread = True

    def start(self):
        self._queue_processor_thread = DaemonThread(target=self._process_queue)

    def draw_network(self):
        nx.draw_networkx(self.network, pos=nx.spring_layout(self.network),
                         with_labels=True, hold=False)
        plt.show()

    def _send_epr(self,sender, receiver):
        route = self.get_route(sender, receiver)
        host_sender = self.get_host(sender)
        receiver_name = self.get_host_name(receiver)
        if len(route) == 2:
            q = host_sender.cqc.createEPR(receiver_name)
            q_id = host_sender.add_epr(receiver, q)
            packet = protocols.encode(sender, receiver, protocols.REC_EPR, payload={'q_id': q_id}, payload_type=protocols.CLASSICAL)
            self.send(packet)
        else:
            for i in range(len(route) - 1):
                self._send_epr(route[i], route[i + 1])

            for i in range(len(route) - 2):
                q = None

                while q is None:
                    q = (self.get_host(route[i + 1])).get_epr(route[0])

                data = {'q': q, 'node': sender, 'type': protocols.EPR}
                protocols._send_teleport(route[i + 1], route[i + 2], data)

            q2 = host_sender.get_epr(route[1])
            host_sender.add_epr(receiver, q2['q'], q2['q_id'])

    def _rec_epr(self,sender, receiver, payload):
        host_receiver = self.get_host(receiver)
        q = host_receiver.cqc.recvEPR()
        host_receiver.add_epr(sender, q, q_id=payload['q_id'])
        return protocols._send_ack(sender, receiver)

    def entanglement_swap(self,sender,receiver):
        route = self.get_route(sender,receiver)
        host_sender = self.get_host(sender)
        receiver_name = self.get_host_name(receiver)
        for i in range(len(route)-1):
            packet = protocols.encode(route[i], route[i+1], protocols.SEND_EPR, payload_type=protocols.SIGNAL)
            time.sleep(5)
            self.send(packet)

        for i in range(len(route) - 2):
            q = None

            while q is None:

                q = (self.get_host(route[i + 1])).get_epr(route[0])

            data = {'q' : q , 'node' : sender , 'type' : protocols.EPR}
            time.sleep(10)
            packet = protocols.encode(route[i+1], route[i+2], protocols.SEND_TELEPORT, data, payload_type=protocols.SIGNAL)
            Logger.get_instance().log(sender + " sends TELEPORT to " + receiver)
            self.send(packet)

        q2 = host_sender.get_epr(route[1])
        host_sender.add_epr(receiver, q2['q'], q2['q_id'])



