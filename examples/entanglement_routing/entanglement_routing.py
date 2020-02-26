import time
import networkx as nx
import random

from components.host import Host
from components.network import Network
from objects.logger import Logger

network = Network.get_instance()


def generate_entanglement(host):
    """
    Generate entanglement if the host has nothing to process (i.e. is idle).
    """
    while True:
        if host.is_idle():
            host_connections = host.get_connections()
            for connection in host_connections:
                if connection['type'] == 'quantum':
                    num_epr_pairs = len(host.get_epr_pairs(connection['connection']))
                    if num_epr_pairs < 5:
                        host.send_epr(connection['connection'], await_ack=True)
        time.sleep(2)


def routing_algorithm(di_graph, source, target):
    """
    Entanglement based routing function. Note: any custom routing function must
    have exactly these three parameters and must return a list ordered by the steps
    in the route.

    Args:
        di_graph (networkx DiGraph): The directed graph representation of the network.
        source (str): The sender ID
        target (str: The receiver ID
    Returns:
        (list): The route ordered by the steps in the route.
    """

    # Generate entanglement network
    entanglement_network = nx.DiGraph()
    nodes = di_graph.nodes()
    for node in nodes:
        host = network.get_host(node)
        host_connections = host.get_connections()
        for connection in host_connections:
            if connection['type'] == 'quantum':
                num_epr_pairs = len(host.get_epr_pairs(connection['connection']))
                # print(host.host_id, connection['connection'], num_epr_pairs)
                if num_epr_pairs == 0:
                    entanglement_network.add_edge(host.host_id, connection['connection'], weight=1000)
                else:
                    entanglement_network.add_edge(host.host_id, connection['connection'], weight=1. / num_epr_pairs)

    try:
        route = nx.shortest_path(entanglement_network, source, target, weight='weight')
        if source == 'A':
            print('-------' + str(route) + '-------')
        return route
    except Exception as e:
        Logger.get_instance().error(e)


def main():
    # network.classical_routing_algo = routing_algorithm
    nodes = ['A', 'node_1', 'node_2', 'B']
    network.use_hop_by_hop = False
    network.set_delay = 0.1
    network.start(nodes)

    A = Host('A')
    A.add_connection('node_1')
    A.add_connection('node_2')
    A.start()

    node_1 = Host('node_1')
    node_1.add_connection('A')
    node_1.add_connection('B')
    node_1.start()

    node_2 = Host('node_2')
    node_2.add_connection('A')
    node_2.add_connection('B')
    node_2.start()

    B = Host('B')
    B.add_connection('node_1')
    B.add_connection('node_2')
    B.start()

    hosts = [A, node_1, node_2, B]
    for h in hosts:
        network.add_host(h)

    node_1.run_protocol(generate_entanglement)
    node_2.run_protocol(generate_entanglement)

    print('---- BUILDING ENTANGLEMENT   ----')
    # Let the network build up entanglement
    for i in range(10):
        print('building...')
        time.sleep(1)
    print('---- DONE BUILDING ENTANGLEMENT   ----')

    network.quantum_routing_algo = routing_algorithm
    choices = ['00', '11', '10', '01']
    for _ in range(5):
        print('----  sending superdense  ----')
        A.send_superdense(B.host_id, random.choice(choices), await_ack=True)
        time.sleep(1)

    print('stopping')
    try:
        network.stop(stop_hosts=True)
    except Exception:
        print('')


if __name__ == '__main__':
    main()
