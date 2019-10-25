from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import networkx as nx
import matplotlib.pyplot as plt

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger
from components.daemon_thread import DaemonThread

network = Network.get_instance()


def generate_entanglement(host):
    while True:
        if host.is_idle():
            host_connections = host.get_connections()
            for connection in host_connections:
                if connection['type'] == 'quantum':
                    w = len(host.get_epr_pairs(connection['connection']))
                    if w < 3:
                        host.send_epr(connection['connection'])
        time.sleep(1)


def routing_algorithm(di_graph, source, target):
    # Generate entanglement network
    entanglement_network = nx.DiGraph()
    nodes = di_graph.nodes()
    for node in nodes:
        host = network.get_host(node)
        host_connections = host.get_connections()
        for connection in host_connections:
            if connection['type'] == 'quantum':
                w = len(host.get_epr_pairs(connection['connection']))
                if w == 0:
                    entanglement_network.add_edge(host.host_id, connection['connection'], weight=1000)
                else:
                    entanglement_network.add_edge(host.host_id, connection['connection'], weight=1. / w)

    try:
        route = nx.shortest_path(entanglement_network, source, target, weight='weight')
        print(route)
        return route
    except Exception as e:
        Logger.get_instance().error(e)


def main():
    # network.quantum_routing_algo = routing_algorithm
    nodes = ['A', 'node_1', 'node_2', 'B']
    network.set_delay = 0.2
    network.start(nodes)

    with CQCConnection("A") as A, CQCConnection("node_1") as node_1, \
            CQCConnection('node_2') as node_2, CQCConnection('B') as B:

        A = Host('A', A)
        A.add_connection('node_1')
        A.start()
        #
        node_1 = Host('node_1', node_1)
        node_1.add_connection('A')
        node_1.add_connection('B')
        node_1.start()

        #
        B = Host('B', B)
        B.add_connection('node_1')
        B.start()
        #
        hosts = [A, node_1, B]
        for h in hosts:
            network.add_host(h)

        # DaemonThread(generate_entanglement, args=(node_1,))

        node_1.send_epr('A', await_ack=True)
        node_1.send_epr('A', await_ack=True)
        node_1.send_epr('B', await_ack=True)
        node_1.send_epr('B', await_ack=True)
        node_1.send_epr('B', await_ack=True)
        node_1.send_epr('B', await_ack=True)

        A.send_superdense(B.host_id, '11')
        A.send_superdense(B.host_id, '00')
        A.send_superdense(B.host_id, '10')
        A.send_superdense(B.host_id, '01')

        # for _ in range():
        #     time.sleep(0.5)
        #     print('send')
        #     A.send_superdense(B.host_id, '10')

        time.sleep(30)
        print('stopping')

        network.stop(stop_hosts=True)


if __name__ == '__main__':
    main()
