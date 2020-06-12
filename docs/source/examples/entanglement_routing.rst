Routing with Entanglement
-------------------------

In this example, we see how to add a custom routing function that considers the entanglement in the network.

We configure the network as follows:

..  code-block:: bash
    :linenos:

    A <==> node_1; A <==> node_2
    B <==> node_1; B <==> node_2

..  code-block:: python
    :linenos:

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


We add a protocol for a Host to constantly generate entanglement.

..  code-block:: python
    :linenos:

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
                        if num_epr_pairs < 4:
                            host.send_epr(connection['connection'], await_ack=True)
            time.sleep(5)


The routing algorithm works as follows.

#) Build a graph with the vertices the Hosts and the edges the connections
#) The weight of each edge is the inverse of the amount of entanglement shared on that link (using a shortest path works best with networkx)
#) When there is no entanglement then add a large weight to that edge
#) Compute the shortest path on this newly generated graph from sender to receiver and return the route

..  code-block:: python
    :linenos:

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

        entanglement_network = nx.DiGraph()
        nodes = di_graph.nodes()
        # Generate entanglement network
        for node in nodes:
            host = network.get_host(node)
            host_connections = host.get_connections()
            for connection in host_connections:
                if connection['type'] == 'quantum':
                    num_epr_pairs = len(host.get_epr_pairs(connection['connection']))
                    if num_epr_pairs == 0:
                        entanglement_network.add_edge(host.host_id, connection['connection'], weight=1000)
                    else:
                        entanglement_network.add_edge(host.host_id, connection['connection'], weight=1. / num_epr_pairs)

        try:
            route = nx.shortest_path(entanglement_network, source, target, weight='weight')
            print('-------' + str(route) + '-------')
            return route
        except Exception as e:
            Logger.get_instance().error(e)

To test the routing, we send superdense messages from A to B after we allow the network to build up some entanglement

..  code-block:: python
    :linenos:

    node_1.run_protocol(generate_entanglement)
    node_2.run_protocol(generate_entanglement)

    print('---- BUILDING ENTANGLEMENT   ----')
    # Let the network build up entanglement
    time.sleep(15)
    print('---- DONE BUILDING ENTANGLEMENT   ----')

    choices = ['00', '11', '10', '01']
    for _ in range(5):
        print('----  sending superdense  ----')
        A.send_superdense(B.host_id, random.choice(choices), await_ack=True)
        time.sleep(1)


The full example is below.

..  code-block:: python
    :linenos:

    from qunetsim.components.host import Host
    from qunetsim.components.network import Network
    from qunetsim.components.logger import Logger
    import networkx
    import time


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
                        if num_epr_pairs < 4:
                            host.send_epr(connection['connection'], await_ack=True)
            time.sleep(5)


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
                    if num_epr_pairs == 0:
                        entanglement_network.add_edge(host.host_id, connection['connection'], weight=1000)
                    else:
                        entanglement_network.add_edge(host.host_id, connection['connection'], weight=1. / num_epr_pairs)

        try:
            route = nx.shortest_path(entanglement_network, source, target, weight='weight')
            print('-------' + str(route) + '-------')
            return route
        except Exception as e:
            Logger.get_instance().error(e)


    def main():
        network = Network.get_instance()
        network.quantum_routing_algo = routing_algorithm
        nodes = ['A', 'node_1', 'node_2', 'B']
        network.use_hop_by_hop = False
        network.set_delay = 0.2
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
        time.sleep(15)
        print('---- DONE BUILDING ENTANGLEMENT   ----')

        choices = ['00', '11', '10', '01']
        for _ in range(5):
            print('----  sending superdense  ----')
            A.send_superdense(B.host_id, random.choice(choices), await_ack=True)
            time.sleep(1)

        # Let the network run for 40 seconds
        time.sleep(40)
        print('stopping')
        network.stop(stop_hosts=True)