Send EPR
--------

In this example, we'll see how to generate a network with 4 nodes as in the figure below.
We'll then send an EPR pair from one end of the link to the other. The example shows
how to build a network and a simple application.

..  code-block:: python

    # Initialize a network
    network = Network.get_instance()

    # Define the host IDs in the network
    nodes = ['Alice', 'Bob', 'Eve', 'Dean']

    # Start the network with the defined hosts
    network.start(nodes)

    # Initialize the host Alice
    host_alice = Host('Alice')

    # Add a one-way connection (classical and quantum) to Bob
    host_alice.add_connection('Bob')

    # Start listening
    host_alice.start()

    host_bob = Host('Bob')
    # Bob adds his own one-way connection to Alice
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.add_connection('Dean')
    host_eve.start()

    host_dean = Host('Dean')
    host_dean.add_connection('Eve')
    host_dean.start()

    # Add the hosts to the network
    # The network is: Alice <--> Bob <--> Eve <--> Dean
    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)

    # Alice generates an EPR pair with Dean and blocks (for a set time)
    # until she receives an ACK from Dean
    q_id = host_alice.send_epr('Dean', await_ack=True)

    # Alice retrieves the EPR pair she sent from her store
    # which has the qubit ID q_id
    q_alice = host_alice.get_epr('Dean', q_id)

    # Dean retrieves the EPR pair Alice sent
    # which has the same qubit ID as Alice's half
    q_dean = host_dean.get_epr('Alice', q_id)

    # Measure the qubits and print the outputs
    m1 = q_alice.measure()
    m2 = q_dean.measure()
    print("Results of the measurements are: (%2d, %2d)" % (m1, m2))

    # Stop the network and the hots
    network.stop(stop_hosts=True)

