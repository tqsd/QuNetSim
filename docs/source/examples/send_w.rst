============
Send W State
============

W state
-------

The W state is an entangled quantum state of three qubits which has the following shape:

    \|W⟩ = 1/√3 (\|001⟩ + \|010⟩ + \|100⟩)

and which is remarkable for representing a specific type of multipartite entanglement and for occurring in several applications in quantum information theory.
The W state is the representative of one of the two non-biseparable classes of three-qubit states (the other being the GHZ state), which cannot be transformed (not even probabilistically) into each other by local quantum operations.
Thus \|W⟩ and \|GHZ⟩ represent two very different kinds of tripartite entanglement.
This difference is, for example, illustrated by the following interesting property of the W state: if one of the three qubits is lost, the state of the remaining 2-qubit system is still entangled. This robustness of W-type entanglement contrasts strongly with the GHZ state, which is fully separable after loss of one qubit.
The states in the W class can be distinguished from all other 3-qubit states by means of multipartite entanglement measures.
In particular, W states have non-zero entanglement across any bipartition, while the 3-tangle vanishes, which is also non-zero for GHZ-type states.

The notion of W state has been generalized for n qubits and then refers to the quantum superpostion with equal expansion coefficients of all possible pure states in which exactly one of the qubits is in an "excited state" \|1⟩, while all other ones are in the "ground state" \|0⟩:

    \|W⟩ = 1/√n (\|0...01⟩ + \|0...010⟩ + ... + \|010...0⟩ + \|10...0⟩)


Example
-------

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

Here, I would like to share a W state between Alice, Bob, Eve and Deve: all I need to do is
to send the entangled state to the other hosts from Alice’s host as shown at line 2.
The send_w() function has an optional parameter (it’s not the only optional one)
named distribute set to False by default that can be used to specify if the sender
should keep part of the GHZ state (False), or just distribute it (True).
After sharing the state, I wait for the acknowledgement of all the participants one by one,
then the system density matrix is printed and a measurement on each participant is performed.

..  code-block:: python
    :linenos:

    share_list = ["Bob", "Eve", "Dean"]
    q_id1, ack_received = host_alice.send_w(share_list, await_ack=True)

    print("Alice received ACK from all? " + str(ack_received))

    q1 = host_alice.get_w('Alice', q_id1, wait=10)
    q2 = host_bob.get_w('Alice', q_id1, wait=10)
    q3 = host_eve.get_w('Alice', q_id1, wait=10)
    q4 = host_dean.get_w('Alice', q_id1, wait=10)

    print("System density matrix:")
    print(q1.density_operator())

    m1 = q1.measure()
    m2 = q2.measure()
    m3 = q3.measure()
    m4 = q4.measure()

    print("\nResults of measurements are %d, %d, %d, %d." % (m1, m2, m3, m4))


The full example is below:

..  code-block:: python
    :linenos:

    from qunetsim.backends import EQSNBackend
    from qunetsim.components import Host
    from qunetsim.components import Network
    from qunetsim.objects import Logger

    Logger.DISABLED = False


    def main():
        network = Network.get_instance()
        nodes = ["Alice", "Bob", "Eve", "Dean"]
        back = EQSNBackend()
        network.start(nodes, back)

        network.delay = 0.1

        host_alice = Host('Alice', back)
        host_alice.add_connection('Bob')
        host_alice.add_connection('Eve')
        host_alice.start()

        host_bob = Host('Bob', back)
        host_bob.add_connection('Alice')
        host_bob.add_connection('Eve')
        host_bob.start()

        host_eve = Host('Eve', back)
        host_eve.add_connection('Bob')
        host_eve.add_connection('Dean')
        host_eve.add_connection('Alice')
        host_eve.start()

        host_dean = Host('Dean', back)
        host_dean.add_connection('Eve')
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        share_list = ["Bob", "Eve", "Dean"]
        q_id1, ack_received = host_alice.send_w(share_list, await_ack=True)

        print("Alice received ACK from all? " + str(ack_received))

        q1 = host_alice.get_w('Alice', q_id1, wait=10)
        q2 = host_bob.get_w('Alice', q_id1, wait=10)
        q3 = host_eve.get_w('Alice', q_id1, wait=10)
        q4 = host_dean.get_w('Alice', q_id1, wait=10)

        print("System density matrix:")
        print(q1.density_operator())

        m1 = q1.measure()
        m2 = q2.measure()
        m3 = q3.measure()
        m4 = q4.measure()

        print("\nResults of measurements are %d, %d, %d, %d." % (m1, m2, m3, m4))

        network.stop(True)
        exit()


    if __name__ == '__main__':
        main()


Example written by: Alessandro Muzzi
