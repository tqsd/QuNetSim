from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import networkx as nx

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
                    edge = (host.host_id, connection['connection'], {'weight': 1000})
                else:
                    edge = (host.host_id, connection['connection'], {'weight': 1. / w})
                entanglement_network.add_edges_from([edge])
    try:
        route = nx.shortest_path(entanglement_network, source=source, target=target, weight='weight')
        print(route)
        return route
    except Exception as e:
        Logger.get_instance().error(e)


def main():
    network.start()
    network.quantum_routing_algo = routing_algorithm

    with CQCConnection("Alice") as A, CQCConnection("Bob") as node_1, \
            CQCConnection('Eve') as node_2, CQCConnection('Dean') as B:

        A = Host('A', A)
        A.add_connection('node_1')
        A.add_connection('node_2')
        A.start()

        node_1 = Host('node_1', node_1)
        node_1.add_connection('A')
        node_1.add_connection('B')
        node_1.start()

        node_2 = Host('node_2', node_2)
        node_2.add_connection('A')
        node_2.add_connection('B')
        node_2.start()

        B = Host('B', B)
        B.add_connection('node_1')
        B.add_connection('node_2')
        B.start()

        hosts = [A, node_1, node_2, B]
        for h in hosts:
            network.add_host(h)

        DaemonThread(generate_entanglement, args=(node_1,))

        time.sleep(5)
        for _ in range(2):
            time.sleep(1)
            print('send')
            A.send_superdense(B.host_id, '10')

        start_time = time.time()

        while time.time() - start_time < 40:
            pass

        for h in hosts:
            h.stop()
        network.stop()


if __name__ == '__main__':
    main()
