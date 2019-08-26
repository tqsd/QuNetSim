import networkx as nx
import matplotlib.pyplot as plt
from components import protocols

from components.logger import Logger


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
            Network.__instance = self
        else:
            raise Exception('this is a singleton class')

    def add_host(self, host):
        Logger.get_instance().log('host added: ' + host.host_id)
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
        return nx.shortest_path(self.network, source=source, target=dest)

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
            'payload_type': payload['payload_type'],
            'TTL': ttl
        }
        return packet

    def transfer_qubits(self, qubits, sender, receiver):
        for q in qubits:
            self.ARP[sender].cqc.sendQubit(q, self.get_host_name(receiver))
            qr = self.ARP[receiver].cqc.recvQubit()
            self.ARP[receiver].add_data_qubit(sender, qr)

    def send(self, packet):
        sender, receiver = packet['sender'], packet['receiver']
        try:
            # TODO: what to do if route doesn't exist?
            route = self.get_route(sender, receiver)
            if len(route) == 2:
                print('sending packet from ' + sender + ' to ' + receiver)
                if packet['protocol'] != protocols.RELAY:
                    self.ARP[receiver].rec_packet(packet)
                else:
                    self.ARP[route[1]].rec_packet(packet['payload'])
            else:
                # Here we're using hop by hop approach
                print('sending relay packet from ' + route[0] + ' to ' + route[1])
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

    def draw_network(self):
        nx.draw_networkx(self.network, pos=nx.spring_layout(self.network),
                         with_labels=True, hold=False)
        plt.show()
