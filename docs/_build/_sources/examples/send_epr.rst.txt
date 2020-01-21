Send EPR Pairs
--------------

In this example, we'll see how to generate a network with 4 nodes as in the figure below.
We'll then send an EPR pair from one end of the link to the other. The example shows
how to build a network and a simple application.


We, as always, first set up the network. Here we form a square grid where classical information
is routed through Host B, and quantum information is routed through Host C. We do this
by specifying the connection type when adding connections to a Host, that is, using methods
*add_c_connection* and *add_q_connection*.

..  code-block:: python
    :linenos:

    network = Network.get_instance()
    nodes = ['A', 'B', 'C']
    network.start(nodes)

    host_A = Host('A')
    host_A.add_connection('B')
    host_A.start()

    host_B = Host('B')
    host_B.add_connection('A')
    host_B.add_connection('C')
    host_B.start()

    host_C = Host('C')
    host_C.add_connection('B')
    host_C.start()

    network.add_host(host_A)
    network.add_host(host_B)
    network.add_host(host_C)

    # Network is A<==>B<==>C;
    # Note: we use 'A<==>B' to represent a classical and quantum connection
    #       we use 'A<-->B' to represent a classical only connection
    #       we use 'A<~~>B' to represent a quantum only connection
    #       All connections are added uni-directionally, so '<' and '>'
    #       represent the direction of the flow of traffic.


Now we define the protocols that should run in the network.

..  code-block:: python
    :linenos:

    # Protocols always need to have the full host as the first parameter.
    def protocol_1(host, receiver):
        """
        Sender protocol for sending 5 EPR pairs.

        Args:
            host (Host): The sender Host.
            receiver (str): The ID of the receiver of the EPR pairs.
        """
        for i in range(5):
            print('Sending EPR pair %d' % (i + 1))
            epr_id, ack_arrived = host.send_epr(receiver, await_ack=True)

            if ack_arrived:
                # Receiver got the EPR pair and ACK came back
                # safe to use the EPR pair.
                q = host.get_epr(receiver, q_id=epr_id)
                print('Host 1 measured: %d' % q.measure())
            else:
                print('The EPR pair was not properly established')
        print('Sender protocol done')



    def protocol_2(host, sender):
        """
        Receiver protocol for receiving 5 EPR pairs.

        Args:
            host (Host): The sender Host.
            sender (str): The ID of the sender of the EPR pairs.
        """

        for _ in range(5):
            # Waits 5 seconds for the EPR to arrive.
            q = host.get_epr(sender, wait=5)
            # q is None if the wait time expired.
            if q is not None:
                print('Host 2 measured: %d' % q.measure())
            else:
                print('Host 2 did not receive an EPR pair')
        print('Receiver protocol done')


Now, we instruct the hosts to run their protocols.

..  code-block:: python
    :linenos:

    host_A.run_protocol(protocol_1, (host_C.host_id,))
    host_C.run_protocol(protocol_2, (host_A.host_id,))



The full example is below.

..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from components.logger import Logger

    Logger.DISABLED = True


    def protocol_1(host, receiver):
        # Here we write the protocol code for a host.
        for i in range(5):
            print('Sending EPR pair %d' % (i + 1))
            epr_id, ack_arrived = host.send_epr(receiver, await_ack=True)

            if ack_arrived:
                # Receiver got the EPR pair and ACK came back
                # safe to use the EPR pair.
                q = host.get_epr(receiver, q_id=epr_id)
                print('Host 1 measured: %d' % q.measure())
            else:
                print('The EPR pair was not properly established')
        print('Sender protocol done')


    def protocol_2(host, sender):
        """
        Receiver protocol for receiving 5 EPR pairs.

        Args:
            host (Host): The sender Host.
            sender (str): The ID of the sender of the EPR pairs.
        """

        # Host 2 waits 5 seconds for the EPR to arrive.
        for _ in range(5):
            q = host.get_epr(sender, wait=5)
            # q is None if the wait time expired.
            if q is not None:
                print('Host 2 measured: %d' % q.measure())
            else:
                print('Host 2 did not receive an EPR pair')
        print('Receiver protocol done')


    def main():
        network = Network.get_instance()
        nodes = ['A', 'B', 'C']
        network.start(nodes)

        host_A = Host('A')
        host_A.add_connection('B')
        host_A.start()

        host_B = Host('B')
        host_B.add_connection('A')
        host_B.add_connection('C')
        host_B.start()

        host_C = Host('C')
        host_C.add_connection('B')
        host_C.start()

        network.add_host(host_A)
        network.add_host(host_B)
        network.add_host(host_C)

        host_A.run_protocol(protocol_1, (host_C.host_id,))
        host_C.run_protocol(protocol_2, (host_A.host_id,))


    if __name__ == '__main__':
        main()
