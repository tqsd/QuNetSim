Eavesdropping on channels
-------------------------

In this example we see how we can add an eavesdropper, or packet sniffer, to the network.
First, as always, we initialize our network:

..  code-block:: python
    :linenos:

    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve"]
    network.start(nodes)
    network.delay = 0.0

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.delay = 0.2
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

Next we can define the protocols for Alice and Eve. First Alice is sending classical messages to Eve and
next prepares qubits in the excited state and also sends them the Eve. Eve simply prints
her messages and measures her qubits.

..  code-block:: python
    :linenos:

    amount_to_transmit = 5
    def alice(host):
        for _ in range(amount_to_transmit):
            s = 'Hi Eve.'
            print("Alice sends: %s" % s)
            host.send_classical('Eve', s, await_ack=True)

        for _ in range(amount_to_transmit):
            print("Alice sends qubit in the |1> state")
            q = Qubit(host)
            q.X()
            host.send_qubit('Eve', q, await_ack=True)

    def eve(host):
        for i in range(amount_to_transmit):
            alice_message = host.get_classical('Alice', wait=5, seq_num=i)
            print("Eve Received classical: %s." % alice_message.content)

        for i in range(amount_to_transmit):
            q = host.get_qubit('Alice', wait=10)
            m = q.measure()
            print("Eve measured: %d." % m)

Now we want to program Bob who sits between Alice and Eve in the network to manipulate
the content of the messages being sent between them. For packets that contain qubits,
Bob performs an :math:`X` operation on them, which will undo Alice's :math:`X` operation.
For packets with classical messages, Bob changes the content so as to let the receiver know
that he saw that message.

..  code-block:: python
    :linenos:

    def bob_sniffing_quantum(sender, receiver, qubit):
        # Bob applies an X operation to all qubits that are routed through him
        qubit.X()


    def bob_sniffing_classical(sender, receiver, msg):
        # Bob modifies the message content of all classical messages routed through him
        msg.content = "** Bob was here :) ** " + msg.content


We set these protocols to the hosts via the following code:

..  code-block:: python
    :linenos:

    host_bob.q_relay_sniffing = True
    host_bob.q_relay_sniffing_fn = eve_sniffing_quantum

    host_bob.c_relay_sniffing = True
    host_bob.c_relay_sniffing_fn = bob_sniffing_classical

    t1 = host_alice.run_protocol(alice)
    t2 = host_eve.run_protocol(eve)

We should see the following output:

..  code-block:: bash
    :linenos:

    Alice sends: Hi Eve.
    Eve Received classical: ** Bob was here :) ** Hi Eve..
    Alice sends: Hi Eve.
    Eve Received classical: ** Bob was here :) ** Hi Eve..
    Alice sends: Hi Eve.
    Eve Received classical: ** Bob was here :) ** Hi Eve..
    Alice sends: Hi Eve.
    Eve Received classical: ** Bob was here :) ** Hi Eve..
    Alice sends: Hi Eve.
    Eve Received classical: ** Bob was here :) ** Hi Eve..
    Alice sends qubit in the |1> state
    Eve measured: 0.
    Alice sends qubit in the |1> state
    Eve measured: 0.
    Alice sends qubit in the |1> state
    Eve measured: 0.
    Alice sends qubit in the |1> state
    Eve measured: 0.
    Alice sends qubit in the |1> state
    Eve measured: 0.

The full example is below.


..  code-block:: python
    :linenos:

    from qunetsim.components import Host
    from qunetsim.components import Network
    from qunetsim.objects import Message
    from qunetsim.objects import Qubit
    from qunetsim.objects import Logger

    Logger.DISABLED = True

    amount_transmit = 5


    def alice(host):
        for _ in range(amount_transmit):
            s = 'Hi Eve.'
            print("Alice sends: %s" % s)
            host.send_classical('Eve', s, await_ack=True)

        for _ in range(amount_transmit):
            print("Alice sends qubit in the |1> state")
            q = Qubit(host)
            q.X()
            host.send_qubit('Eve', q, await_ack=True)


    def bob_sniffing_quantum(sender, receiver, qubit):
        # Bob applies an X operation to all qubits that are routed through him
        qubit.X()


    def bob_sniffing_classical(sender, receiver, msg):
        # Bob modifies the message content of all classical messages routed through him
        if isinstance(msg, Message):
            msg.content = "** Bob was here :) ** " + msg.content


    def eve(host):
        for i in range(amount_transmit):
            alice_message = host.get_classical('Alice', wait=5, seq_num=i)
            print("Eve Received classical: %s." % alice_message.content)

        for i in range(amount_transmit):
            q = host.get_qubit('Alice', wait=10)
            m = q.measure()
            print("Eve measured: %d." % m)


    def main():
        network = Network.get_instance()
        nodes = ["Alice", "Bob", "Eve"]
        network.start(nodes)
        network.delay = 0.0

        host_alice = Host('Alice')
        host_alice.add_connection('Bob')
        host_alice.start()

        host_bob = Host('Bob')
        host_bob.add_connection('Alice')
        host_bob.add_connection('Eve')
        host_bob.start()

        host_eve = Host('Eve')
        host_eve.add_connection('Bob')
        host_eve.delay = 0.2
        host_eve.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        host_bob.q_relay_sniffing = True
        host_bob.q_relay_sniffing_fn = eve_sniffing_quantum

        host_bob.c_relay_sniffing = True
        host_bob.c_relay_sniffing_fn = bob_sniffing_classical

        t1 = host_alice.run_protocol(alice)
        t2 = host_eve.run_protocol(eve)

        t1.join()
        t2.join()

        network.stop(True)
        exit()


    if __name__ == '__main__':
        main()
