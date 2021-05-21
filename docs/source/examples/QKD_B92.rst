Quantum Key Distribution - B92
-------------------------------
The Quantum Key Distribution B92 protocol was proposed in 1992 by Charles Bennett. It is a modified version of the BB84 protocol.
This protocol is different from the BB84 in the following ways:

* It uses two possible states of qubits being sent instead of four
* Alice and Bob do not need to compare bases at any point.

First, we create a network with three hosts, Alice, Bob and Eve. Alice will send her qubits to Bob and Eve will, or will not, eavesdrop and manipulate the qubits she intercepts.
The network will link Alice to Eve, Eve to Alice and Bob, and Bob to Eve.
Here is also the place to define which function will Eve run if the eavesdropping is turned on.

..  code-block:: python
    :linenos:
    def build_network_b92(eve_interception):

    network = Network.get_instance()

    nodes = ['Alice','Bob','Eve']
    network.start(nodes)

    host_alice = Host('Alice')
    host_bob = Host('Bob')
    host_eve = Host('Eve')

    host_alice.add_connection('Eve')
    host_eve.add_connection('Alice')
    host_eve.add_connection('Bob')
    host_bob.add_connection('Eve')
    #adding the connections - Alice wants to transfer an encrypted message to Bob
    #The network looks like this: Alice---Eve---Bob

    host_alice.delay = 0.3
    host_bob.delay = 0.3

    #starting
    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    if eve_interception == True:
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

    hosts = [host_alice,host_bob,host_eve]
    print('Made a network!')
    return network, hosts


