Send Data Qubits
----------------

In this example, we send a data qubit from Alice to Dean who sits 2 hops away from Alice in the network.


First we configure the network.

..  code-block:: python
    :linenos:

    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
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

    # Network will be:
    # Alice <==> Bob <==> Eve <==> Dean
    # Note: we use 'A<==>B' to represent a classical and quantum connection
    #       we use 'A<-->B' to represent a classical only connection
    #       we use 'A<~~>B' to represent a quantum only connection
    #       All connections are added uni-directionally, so '<' and '>'
    #       represent the direction of the flow of traffic.


    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)


Now, the Host Alice will send 10 qubits to Dean after applying an *X* gate on the qubit.
She will then wait for an acknowledgement from Dean before continuing, that is, line 7 below will
block until an *ACK* arrives at Alice. Alice has a setting, *Host.max_ack_wait*, that tells her to wait
for the set time before assuming that either the packet didn't arrive at Dean, or the ACK was lost. Because the flag
*await_ack* is set to true, *send_qubit* will return two values: the qubit ID that was sent, and
a boolean value that says if the *ACK* arrived, or Alice exceeded the maximum waiting time.

In QuNetSim, there are two ways of writing protocols. Here we see what we will call the *linear* style. What
this means is that all of the hosts are being accessed at the same place in the code. In the next example, we will see
what we will call a *parallel* style, where the programmer of the simulation has access to one host at a time, and
has to add logic to the protocol to transmit needed information to the communicating parties. Each host will run their
part of the protocol, but can't access any information from other hosts directly.

With this in mind, we see that on line 10, because Alice awaited the *ACK* from Dean, and line 7 is blocking,
Dean can safely access the qubit that Alice sent without having to wait.

..  code-block:: python
    :linenos:

    for _ in range(10):
        # Create a qubit owned by Alice
        q = Qubit(host_alice)
        # Put the qubit in the excited state
        q.X()
        # Send the qubit and await an ACK from Dean
        q_id, ack_arrived = host_alice.send_qubit('Dean', q, await_ack=True)

        # Get the qubit on Dean's side from Alice
        q_rec = host_dean.get_data_qubit('Alice', q_id, wait=0)

        # Ensure the qubit arrived and then measure and print the results.
        if q_rec is not None:
            m = q_rec.measure()
            print("Results of the measurements for q_id are ", str(m))
        else:
            print('Qubit did not arrive.')

In the next example, we'll see something similar using the parallel style.

The full example is below:

..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from objects.qubit import Qubit


    def main():
        network = Network.get_instance()
        nodes = ["Alice", "Bob", "Eve", "Dean"]
        network.start(nodes)
        network.delay = 0.1

        host_alice = Host('Alice')
        host_alice.add_connection('Bob')
        host_alice.start()

        host_bob = Host('Bob')
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

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        for _ in range(10):
            # Create a qubit owned by Alice
            q = Qubit(host_alice)
            # Put the qubit in the excited state
            q.X()
            # Send the qubit and await an ACK from Dean
            q_id, _ = host_alice.send_qubit('Dean', q, await_ack=True)

            # Get the qubit on Dean's side from Alice
            q_rec = host_dean.get_data_qubit('Alice', q_id)

            # Ensure the qubit arrived and then measure and print the results.
            if q_rec is not None:
                m = q_rec.measure()
                print("Results of the measurements for q_id are ", str(m))
            else:
                print('q_rec is none')

        # Stop the network at the end of the example
        network.stop(stop_hosts=True)

    if __name__ == '__main__':
        main()

