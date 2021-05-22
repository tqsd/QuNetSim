Quantum Key Distribution - B92
-------------------------------
The Quantum Key Distribution B92 protocol was proposed in 1992 by Charles Bennett. It is a modified version of the BB84 protocol.
This protocol is different from the BB84 in the following ways:

1. It uses two possible states of qubits being sent instead of four.
2. Alice and Bob do not need to compare bases at any point.

A detailed description of this protocol can be found `here <http://www.rri.res.in/quic/qkdactivities.php>`__

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

First, a random encryption key of a certain length is generated. The key is a list of binary numbers.

..  code-block:: python
    :linenos:

    def generate_key(key_length):
        generated_key = []
        for i in range(key_length):
            generated_key.append(randint(0,1))
            print(f'Generated the key {generated_key}')
        return generated_key

We now implement the B92 protocol. For each bit in the encrypted key, Alice generates and sends a qubit to Bob.
If the bit she wants to send is 0, she sends a :math:`|0\rangle`, and if the bit is 1, she sends :math:`|+\rangle`.

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
                    #if, however, message says Bob failed to measure the qubit, 
                    #Alice will resend it.


Bob receives the qubit Alice sent, and randomly chooses a base (rectilinear or diagonal) for the qubit measurement.
If he chooses the rectilinear basis, and the measurement yields the state :math:`|1\rangle`, then Bob knows that Eve's qubit was :math:`|+\rangle`, and therefore the bit she sent was 1. 
Bob sends Alice a classical message after the measurement and tells her whether he succeeded or failed to extract the information.

..  code-block:: python
    :linenos:

    def receiver_qkd(bob, key_size, sender):
        key_array = []
        received_counter = 0
        #counts the key bits successfully measured by Bob
        while received_counter < key_size:
            base = randint(0,1)
                 #0 means rectilinear basis and 1 means diagonal basis
            qubit = bob.get_data_qubit(sender,wait = wait_time)
            if qubit is not None:
                if base == 1:
                    qubit.H()
                bit = qubit.measure()
                if bit == 1:
                    if base == 1:
                        resulting_key_bit = 0
                    elif base == 0:
                        resulting_key_bit = 1
                    message_to_send = 'qubit successfully acquired'
                    key_array.append(resulting_key_bit) 
                    received_counter += 1 
                    print(f'Bob received qubit {received_counter}')
                else:
                    message_to_send = 'fail'
                bob.send_classical(sender,message_to_send, await_ack = True) 
        return key_array

After sending all of the bits of the encrypted key, Alice and Bob should check whether Eve eavesdropped on the channel.
For this purpose, each of them takes for comparison a certain part of the encrypted key they have. 
Alice classically sends part of the key she has to Bob. He compares it to the part he has. If it's the same information, he sends her a message informing her that the key was transferred without eavesdropping. If, however, the part he receives is different from what he has, it means eavesdropping occurred and he sends a message to inform Alice about it. 

..  code-block:: python
    :linenos:

    def check_key_sender(alice, key_check_alice, receiver):
        key_check_string = ''.join([str(x) for x in key_check_alice])
        print(f'Alice\'s key to check is {key_check_string}')
        alice.send_classical(receiver,key_check_string,await_ack = True)
        message_from_bob = alice.get_next_classical(receiver, wait = -1)
        #Bob tells Alice whether the key part is the same at his end.
        #If not - it means Eve eavesdropped. 
        if message_from_bob is not None:
            if message_from_bob.content == 'Success':
                print('Key is successfully verified')
            elif message_from_bob.content == 'Fail':
                print('Key has been corrupted')

..  code-block:: python
    :linenos:

    def check_key_receiver(bob, key_check_bob,sender):
        key_check_bob_string = ''.join([str(x) for x in key_check_bob])
        print(f'Bob\'s key to check is {key_check_bob_string}')
        key_from_alice = bob.get_next_classical(sender, wait = -1)
        if key_from_alice is not None:
            if key_from_alice.content == key_check_bob_string:
                bob.send_classical(sender,'Success',await_ack = True)
            else:
                bob.send_classical(sender,'Fail',await_ack = True)



If the eavesdropping is turned on, Eve runs the function eve_sniffing_quantum. She intercepts a qubit that is sent from Alice to Bob. She measures the qubit with probability 0.5. 
For the measurement of the qubit, she randomly chooses the basis (rectilinear or diagonal).

..  code-block:: python
    :linenos:

    def eve_sniffing_quantum(sender,receiver,qubit):
        #Eve will manipulate only part of the qubits she intercepts
        #She chooses the base in which she measures at random.
        if sender == 'Alice':
            r = random()
            if r > 0.5:
                base = randint(0,1)
                if base == 1:
                    qubit.H()
                qubit.measure(non_destructive = True)


The full example is given below.

..  code-block:: python
    :linenos:

    from qunetsim.components import Host, Network
    from qunetsim.objects import Qubit
    from qunetsim.objects import Logger
    from random import randint, random

    Logger.DISABLED = True
    wait_time = 60

    def eve_sniffing_quantum(sender,receiver,qubit):
        #Eve will manipulate only part of the qubits she intercepts
        #She chooses the base in which she measures at random.
        if sender == 'Alice':
            r = random()
            if r > 0.5:
                base = randint(0,1)
                if base == 1:
                    qubit.H()
                qubit.measure(non_destructive = True)


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


    def generate_key(key_length):
        generated_key = []
        for i in range(key_length):
            generated_key.append(randint(0,1))
        print(f'Generated the key {generated_key}')
        return generated_key


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
                    #if, however, message says Bob failed to measure the qubit, 
                    #Alice will resend it.
        

    def receiver_qkd(bob, key_size, sender):
        key_array = []
        received_counter = 0
        #counts the key bits successfully measured by Bob
        while received_counter < key_size:
            base = randint(0,1)
           #0 means rectilinear basis and 1 means diagonal basis
            qubit = bob.get_data_qubit(sender,wait = wait_time)
            if qubit is not None:
                if base == 1:
                    qubit.H()
                bit = qubit.measure()
                if bit == 1:
                    if base == 1:
                        resulting_key_bit = 0
                    elif base == 0:
                        resulting_key_bit = 1
                    message_to_send = 'qubit successfully acquired'
                    key_array.append(resulting_key_bit) 
                    received_counter += 1 
                    print(f'Bob received qubit {received_counter}')
                else:
                    message_to_send = 'fail'
                bob.send_classical(sender,message_to_send, await_ack = True) 
        return key_array


    def check_key_sender(alice, key_check_alice, receiver):
        key_check_string = ''.join([str(x) for x in key_check_alice])
        print(f'Alice\'s key to check is {key_check_string}')
        alice.send_classical(receiver,key_check_string,await_ack = True)
        message_from_bob = alice.get_next_classical(receiver, wait = -1)
        #Bob tells Alice whether the key part is the same at his end.
        #If not - it means Eve eavesdropped. 
        if message_from_bob is not None:
            if message_from_bob.content == 'Success':
                print('Key is successfully verified')
            elif message_from_bob.content == 'Fail':
                print('Key has been corrupted')


    def check_key_receiver(bob, key_check_bob,sender):
        key_check_bob_string = ''.join([str(x) for x in key_check_bob])
        print(f'Bob\'s key to check is {key_check_bob_string}')
        key_from_alice = bob.get_next_classical(sender, wait = -1)
        if key_from_alice is not None:
            if key_from_alice.content == key_check_bob_string:
                bob.send_classical(sender,'Success',await_ack = True)
            else:
                bob.send_classical(sender,'Fail',await_ack = True)


    def alice_func(host, bob_id, length_of_check, key_length):
        encryption_key_binary = generate_key(key_length)
        sender_qkd(host, encryption_key_binary, bob_id)
        print('Sent all the qubits sucessfully!')
        key_to_test = encryption_key_binary[0:length_of_check]
        check_key_sender(host, key_to_test ,bob_id)


    def bob_func(host, alice_id, length_of_check, key_length):
        secret_key_bob = receiver_qkd(host, key_length, alice_id)
        key_to_test = secret_key_bob[0:length_of_check]
        check_key_receiver(host, key_to_test, alice_id)


    def b92_protocol(eve_interception, key_length, length_of_check):
        network, hosts = build_network_b92(eve_interception)
        alice = hosts[0]
        bob = hosts[1]
        bob_id = bob.host_id
        alice_id = alice.host_id

        thread_1 = alice.run_protocol(alice_func,(bob_id, length_of_check, key_length,))
        thread_2 = bob.run_protocol(bob_func,(alice_id, length_of_check, key_length,))

        thread_1.join()
        thread_2.join()

        network.stop(True)
        exit()


    if __name__ == '__main__':
        key_length = 10
        length_of_check = round(key_length/2)
        #length of part of the key used to check whether Eve listened 
        eve_interception = True
        #the eavesdropping can be turned on and off
        b92_protocol(eve_interception, key_length, length_of_check)
