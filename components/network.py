import networkx as nx
import matplotlib.pyplot as plt
from components import protocols


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

    def _decode_packet(self, packet):
        return packet[0][0:8], packet[0][8:16]

    def _send_network_packet(self, src, dest, link_layer_packet):
        network_packet = protocols.encode(src, dest, protocols.RELAY, link_layer_packet, protocols.SIGNAL)
        self.ARP[dest].rec_packet(network_packet)

        return None

    def send(self, packet):
        sender, receiver = self._decode_packet(packet)
        route = self.get_route(sender, receiver)


        self.ARP[receiver].rec_packet(packet)

    def draw_network(self):
        nx.draw_networkx(self.network, pos=nx.spring_layout(self.network),
                         with_labels=True, hold=False)
        plt.show()
