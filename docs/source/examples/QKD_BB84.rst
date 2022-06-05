Quantum Key Distribution - BB84
-------------------------------

In this example, we'll see how the Quantum Key Distribution algorithm can be
implemented using QuNetSim. First, we create a network of three different parties:
Alice, Bob, and Eve. In the topology of the network, Alice can talk to Bob and Bob
can talk to Eve.

..  code-block:: python
    :linenos:

    import numpy as np

    # Initialize a network
    network = Network.get_instance()

    # Define the host IDs in the network
    nodes = ['Alice', 'Bob', 'Eve']

    # Start the network with the defined hosts
    network.start(nodes)

    # Initialize the host Alice
    host_alice = Host('Alice')

    # Add a one-way connection (classical and quantum) to Bob
    host_alice.add_connection('Bob')

    # Start listening
    host_alice.start()

    host_bob = Host('Bob')
    # Bob adds his own one-way connection to Alice and Eve
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.start()

    # Add the hosts to the network
    # The network is: Alice <--> Bob <--> Eve
    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)


Alice now wants to communicate securely to Eve, without Bob beeing able to read
their communication. To do so, Alice and Eve first want to share a secret key.
Once they have the key, they can use a pre shared key protocol, such as AES
(see `here <https://en.wikipedia.org/wiki/Advanced_Encryption_Standard>`__)
to communicate securely with each other. However, sharing the key is not trivial.
The QKD algorithm solves this problem. If you are not familiar with it yet,
see `here <https://en.wikipedia.org/wiki/BB84>`__.

First, Alice has to create a random key which she can then share with Eve.

..  code-block:: python
    :linenos:

    key_size = 10 # the size of the key in bit
    secret_key = np.random.randint(2, size=key_size)

We now implement the protocols used by Alice and Eve.
Alice randomly decides in which basis she sends her bits. She either chooses
the \|0\> \|1\> basis or the \|+\> \|-\> basis. Eve also chooses a random basis in which
she measures the qubit. She then sends a classical message to Alice, in which basis
she has measured her qubit. Alice then checks if the basis have matched and sends the result
to Eve. If they have matched, she continues with the next bit. Otherwise, she repeats
the same bit again, until the transmission works.

..  code-block:: python
    :linenos:

    def alice_qkd(alice, msg_buff, secret_key, receiver):
        sequence_nr = 0
        # iterate over all bits in the secret key.
        for bit in secret_key:
            ack = False
            while not ack:
                print("Alice sent %d key bits" % (sequence_nr + 1))
                # get a random base. 0 for Z base and 1 for X base.
                base = random.randint(0, 1)

                # create qubit
                q_bit = Qubit(alice)

                # Set qubit to the bit from the secret key.
                if bit == 1:
                    q_bit.X()

                # Apply basis change to the bit if necessary.
                if base == 1:
                    q_bit.H()

                # Send Qubit to Bob
                alice.send_qubit(receiver, q_bit, await_ack=True)

                # Get measured basis of Bob
                message = alice.get_next_classical_message(receiver, msg_buff, sequence_nr)

                # Compare to send basis, if same, answer with 0 and set ack True and go to next bit,
                # otherwise, send 1 and repeat.
                if message == ("%d:%d") % (sequence_nr, base):
                    ack = True
                    alice.send_classical(receiver, ("%d:0" % sequence_nr), await_ack=True)
                else:
                    ack = False
                    alice.send_classical(receiver, ("%d:1" % sequence_nr), await_ack=True)

                sequence_nr += 1

    def eve_qkd(eve, msg_buff, key_size, sender):
        sequence_nr = 0
        received_counter = 0
        key_array = []

        while received_counter < key_size:
            # decide for a measurement base
            measurement_base = random.randint(0, 1)

            # wait for the qubit
            q_bit = eve.get_qubit(sender, wait=wait_time)
            while q_bit is None:
                q_bit = eve.get_qubit(sender, wait=wait_time)

            # measure qubit in right measurement basis
            if measurement_base == 1:
                q_bit.H()
            bit = q_bit.measure()

            # Send Alice the base in which Bob has measured
            eve.send_classical(sender, "%d:%d" % (sequence_nr, measurement_base), await_ack=True)

            # get the return message from Alice, to know if the bases have matched
            msg = eve.get_next_classical_message(sender, msg_buff, sequence_nr)

            # Check if the bases have matched
            if msg == ("%d:0" % sequence_nr):
                received_counter += 1
                print("Eve received %d key bits." % received_counter)
                key_array.append(bit)
            sequence_nr += 1

        return key_array

In the end, Alice and Eve should have the same key. What they still need are an
encryption and decryption function to encrypt and decrypt their messages. Because
our key is too small to use a real encryption function, we will define our own one:

..  code-block:: python
    :linenos:

    # !! Warning: this Crypto algorithm is really bad!
    # !! Warning: Do not use it as a real Crypto Algorithm!

    # key has to be a string
    def encrypt(key, text):
    encrypted_text = ""
        for char in text:
            encrypted_text += chr(ord(key)^ord(char))
        return encrypted_text

    def decrypt(key, encrypted_text):
        return encrypt(key, encrypted_text)

    # Test the encryption algorithm
    print(decrypt('a', decrypt('a', "Encryption works!")))

Alice can finally send her message to Eve, without being disturbed by Bob!

..  code-block:: python
    :linenos:

    # helper function, used to make the key to a string
    def key_array_to_key_string(key_array):
        key_string_binary = ''.join([str(x) for x in key_array])
        return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(key_string_binary)] * 8))


    def alice_send_message(alice, secret_key, receiver):
        msg_to_eve = "Hi Eve, how are you???"
        secret_key_string = key_array_to_key_string(secret_key)
        encrypted_msg_to_eve = encrypt(secret_key_string, msg_to_eve)
        print("Alice sends encrypted message")
        alice.send_classical(receiver, "-1:" + encrypted_msg_to_eve, await_ack=True)


    def eve_receive_message(eve, msg_buff, eve_key, sender):
        encrypted_msg_from_alice = eve.get_next_classical_message(sender, msg_buff, -1)
        encrypted_msg_from_alice = encrypted_msg_from_alice.split(':')[1]
        secret_key_string = key_array_to_key_string(eve_key)
        decrypted_msg_from_alice = decrypt(secret_key_string, encrypted_msg_from_alice)
        print("Eve received decoded message: %s" % decrypted_msg_from_alice)


We can now concatenate the two actions of Alice and Eve and let them each run in their own thread.

..  code-block:: python
    :linenos:

    # Concatentate functions
    def alice_func(alice):
        msg_buff = []
        alice_qkd(alice, msg_buff, secret_key, host_eve.host_id)
        alice_send_message(alice, secret_key, host_eve.host_id)

    def eve_func(eve):
        msg_buff = []
        eve_key = eve_qkd(eve, msg_buff, key_size, host_alice.host_id)
        eve_receive_message(eve, msg_buff, eve_key, host_alice.host_id)

    # Run Bob and Alice

    t1 = host_alice.run_protocol(alice_func, ())
    t2 = host_eve.run_protocol(eve_func, ())

    t1.join()
    t2.join()



The full example is below:

..  code-block:: python
    :linenos:

    import numpy as np
    import random

    from qunetsim.components import Host
    from qunetsim.components import Network
    from qunetsim.objects import Qubit
    from qunetsim.objects import Logger

    Logger.DISABLED = True

    wait_time = 10


    # !! Warning: this Crypto algorithm is really bad!
    # !! Warning: Do not use it as a real Crypto Algorithm!

    # key has to be a string
    def encrypt(key, text):
        encrypted_text = ""
        for char in text:
            encrypted_text += chr(ord(key) ^ ord(char))
        return encrypted_text


    def decrypt(key, encrypted_text):
        return encrypt(key, encrypted_text)


    def alice_qkd(alice, msg_buff, secret_key, receiver):
        sequence_nr = 0
        # iterate over all bits in the secret key.
        for bit in secret_key:
            ack = False
            while not ack:
                print("Alice sent %d key bits" % (sequence_nr + 1))
                # get a random base. 0 for Z base and 1 for X base.
                base = random.randint(0, 1)

                # create qubit
                q_bit = Qubit(alice)

                # Set qubit to the bit from the secret key.
                if bit == 1:
                    q_bit.X()

                # Apply basis change to the bit if necessary.
                if base == 1:
                    q_bit.H()

                # Send Qubit to Bob
                alice.send_qubit(receiver, q_bit, await_ack=True)

                # Get measured basis of Bob
                message = alice.get_next_classical_message(receiver, msg_buff, sequence_nr)

                # Compare to send basis, if same, answer with 0 and set ack True and go to next bit,
                # otherwise, send 1 and repeat.
                if message == ("%d:%d") % (sequence_nr, base):
                    ack = True
                    alice.send_classical(receiver, ("%d:0" % sequence_nr), await_ack=True)
                else:
                    ack = False
                    alice.send_classical(receiver, ("%d:1" % sequence_nr), await_ack=True)

                sequence_nr += 1


    def eve_qkd(eve, msg_buff, key_size, sender):
        sequence_nr = 0
        received_counter = 0
        key_array = []

        while received_counter < key_size:
            # decide for a measurement base
            measurement_base = random.randint(0, 1)

            # wait for the qubit
            q_bit = eve.get_qubit(sender, wait=wait_time)
            while q_bit is None:
                q_bit = eve.get_qubit(sender, wait=wait_time)

            # measure qubit in right measurement basis
            if measurement_base == 1:
                q_bit.H()
            bit = q_bit.measure()

            # Send Alice the base in which Bob has measured
            eve.send_classical(sender, "%d:%d" % (sequence_nr, measurement_base), await_ack=True)

            # get the return message from Alice, to know if the bases have matched
            msg = eve.get_next_classical_message(sender, msg_buff, sequence_nr)

            # Check if the bases have matched
            if msg == ("%d:0" % sequence_nr):
                received_counter += 1
                print("Eve received %d key bits." % received_counter)
                key_array.append(bit)
            sequence_nr += 1

        eve_key = key_array

        return eve_key


    # helper function, used to make the key to a string
    def key_array_to_key_string(key_array):
        key_string_binary = ''.join([str(x) for x in key_array])
        return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(key_string_binary)] * 8))


    def alice_send_message(alice, secret_key, receiver):
        msg_to_eve = "Hi Eve, how are you???"
        secret_key_string = key_array_to_key_string(secret_key)
        encrypted_msg_to_eve = encrypt(secret_key_string, msg_to_eve)
        print("Alice sends encrypted message")
        alice.send_classical(receiver, "-1:" + encrypted_msg_to_eve, await_ack=True)


    def eve_receive_message(eve, msg_buff, eve_key, sender):
        encrypted_msg_from_alice = eve.get_next_classical_message(sender, msg_buff, -1)
        encrypted_msg_from_alice = encrypted_msg_from_alice.split(':')[1]
        secret_key_string = key_array_to_key_string(eve_key)
        decrypted_msg_from_alice = decrypt(secret_key_string, encrypted_msg_from_alice)
        print("Eve received decoded message: %s" % decrypted_msg_from_alice)


    def main():
        # Initialize a network
        network = Network.get_instance()

        # Define the host IDs in the network
        nodes = ['Alice', 'Bob', 'Eve']

        network.delay = 0.0

        # Start the network with the defined hosts
        network.start(nodes)

        # Initialize the host Alice
        host_alice = Host('Alice')

        # Add a one-way connection (classical and quantum) to Bob
        host_alice.add_connection('Bob')

        # Start listening
        host_alice.start()

        host_bob = Host('Bob')
        # Bob adds his own one-way connection to Alice and Eve
        host_bob.add_connection('Alice')
        host_bob.add_connection('Eve')
        host_bob.start()

        host_eve = Host('Eve')
        host_eve.add_connection('Bob')
        host_eve.start()

        # Add the hosts to the network
        # The network is: Alice <--> Bob <--> Eve
        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        # Generate random key
        key_size = 10  # the size of the key in bit
        secret_key = np.random.randint(2, size=key_size)

        # Concatentate functions
        def alice_func(alice):
            msg_buff = []
            alice_qkd(alice, msg_buff, secret_key, host_eve.host_id)
            alice_send_message(alice, secret_key, host_eve.host_id)

        def eve_func(eve):
            msg_buff = []
            eve_key = eve_qkd(eve, msg_buff, key_size, host_alice.host_id)
            eve_receive_message(eve, msg_buff, eve_key, host_alice.host_id)

        # Run Bob and Alice

        t1 = host_alice.run_protocol(alice_func, ())
        t2 = host_eve.run_protocol(eve_func, ())

        t1.join()
        t2.join()


    if __name__ == '__main__':
        main()
