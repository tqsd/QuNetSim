Quantum Key Distribution - B92
-------------------------------
The Quantum Key Distribution B92 protocol was proposed in 1992 by Charles Bennett. It is a modified version of the BB84 protocol.
This protocol is different from the BB84 in the following ways:

* It uses two possible states of qubits being sent instead of four
* Alice and Bob do not need to compare bases at any point.

A detailed description of this protocol can be found `here <http://www.rri.res.in/quic/qkdactivities.php>`

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

Also, a random key of a certain length is generated. The key is a list of binary numbers.

..  code-block:: python
    :linenos:

    def generate_key(key_length):
        generated_key = []
        for i in range(key_length):
            generated_key.append(randint(0,1))
            print(f'Generated the key {generated_key}')
        return generated_key

We now implement the B92 protocol. For each bit in the encrypted key, Alice generates and sends a qubit to Bob.
If the bit she wants to send is 0, she sends a \|0\>, and if the bit is 1, she sends \|+\>.

Then, after she sends the qubit, she waits for a (classical) message from Bob.
If Bob tells her he measured the qubit and extracted the information, she prepares and sends the next one. 
Otherwise, she sends the information concerning this bit again and again, until a confirmation is received. 

..  code-block:: python
    :linenos:

    def sender_qkd(alice, secret_key, receiver):
        sent_qubit_counter = 0
        for bit in secret_key:
            success = False
            while success == False:
                qubit = Qubit(alice)
                if bit == 1:
                    qubit.H()
                #If we want to send 0, we'll send |0>
                #If we want to send 1, we'll send |+>
                alice.send_qubit(receiver, qubit, await_ack = True)
                message = alice.get_next_classical(receiver, wait = -1)
                if message is not None:
                    if message.content == 'qubit successfully acquired':
                        print(f'Alice sent qubit {sent_qubit_counter+1} to Bob')
                        success = True
                        sent_qubit_counter += 1
                    #if, however, message says Bob failed to measure the qubit, Alice will resend it.



