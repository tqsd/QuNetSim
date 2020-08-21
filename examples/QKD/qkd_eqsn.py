import numpy as np
import random
import time

from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
from qunetsim.backends import EQSNBackend

Logger.DISABLED = True

wait_time = 10


# !! Warning: this Crypto algorithm is really bad!
# !! Warning: Do not use it as a real Crypto Algorithm!

# key has to be a string
def encrypt(key, text):
    encrypted_text = ""
    for char in text:
        encrypted_text += chr(ord(key[0]) ^ ord(char))
    return encrypted_text


def decrypt(key, encrypted_text):
    return encrypt(key, encrypted_text)


def get_next_classical_message(host, receive_from_id, buffer, sequence_nr):
    buffer = buffer + host.get_classical(receive_from_id, wait=-1)
    msg = "ACK"
    while msg == "ACK" or (msg.split(':')[0] != ("%d" % sequence_nr)):
        if len(buffer) == 0:
            buffer = buffer + host.get_classical(receive_from_id, wait=-1)
        ele = buffer.pop(0)
        msg = ele.content
    return msg


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
            message = get_next_classical_message(
                alice, receiver, msg_buff, sequence_nr)

            # Compare to send basis, if same, answer with 0 and set ack True and go to next bit,
            # otherwise, send 1 and repeat.
            if message == ("%d:%d") % (sequence_nr, base):
                ack = True
                alice.send_classical(receiver, ("%d:0" %
                                                sequence_nr), await_ack=True)
            else:
                ack = False
                alice.send_classical(receiver, ("%d:1" %
                                                sequence_nr), await_ack=True)

            sequence_nr += 1


def eve_qkd(eve, msg_buff, key_size, sender):
    sequence_nr = 0
    received_counter = 0
    key_array = []

    while received_counter < key_size:
        # decide for a measurement base
        measurement_base = random.randint(0, 1)

        # wait for the qubit
        q_bit = eve.get_data_qubit(sender, wait=wait_time)
        while q_bit is None:
            q_bit = eve.get_data_qubit(sender, wait=wait_time)

        # measure qubit in right measurement basis
        if measurement_base == 1:
            q_bit.H()
        bit = q_bit.measure()

        # Send Alice the base in which Bob has measured
        eve.send_classical(sender, "%d:%d" %
                           (sequence_nr, measurement_base), await_ack=True)

        # get the return message from Alice, to know if the bases have matched
        msg = get_next_classical_message(eve, sender, msg_buff, sequence_nr)

        # Check if the bases have matched
        if msg == ("%d:0" % sequence_nr):
            received_counter += 1
            print("Eve received %d key bits." % received_counter)
            key_array.append(bit)
        sequence_nr += 1
    return key_array


# helper function, used to make the key to a string
def key_array_to_key_string(key_array):
    key_string_binary = ''.join([str(x) for x in key_array])
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(key_string_binary)] * 8))


def alice_send_message(alice, secret_key, receiver):
    msg_to_eve = "Hi Eve, how are you?"
    secret_key_string = key_array_to_key_string(secret_key)
    encrypted_msg_to_eve = encrypt(secret_key_string, msg_to_eve)
    print("Alice sends encrypted message")
    alice.send_classical(
        receiver, "-1:" + encrypted_msg_to_eve, await_ack=True)


def eve_receive_message(eve, msg_buff, eve_key, sender):
    encrypted_msg_from_alice = get_next_classical_message(
        eve, sender, msg_buff, -1)
    encrypted_msg_from_alice = encrypted_msg_from_alice.split(':')[1]
    secret_key_string = key_array_to_key_string(eve_key)
    decrypted_msg_from_alice = decrypt(
        secret_key_string, encrypted_msg_from_alice)
    print("Eve received decoded message: %s" % decrypted_msg_from_alice)


def main():
    # Initialize a network
    network = Network.get_instance()
    backend = EQSNBackend()

    # Define the host IDs in the network
    nodes = ['Alice', 'Bob']

    network.delay = 0.0

    # Start the network with the defined hosts
    network.start(nodes, backend)

    # Initialize the host Alice
    host_alice = Host('Alice', backend)

    # Add a one-way connection (classical and quantum) to Bob
    host_alice.add_connection('Bob')
    host_alice.delay = 0.0

    # Start listening
    host_alice.start()

    host_bob = Host('Bob', backend)
    # Bob adds his own one-way connection to Alice
    host_bob.add_connection('Alice')
    host_bob.delay = 0.0
    host_bob.start()

    # Add the hosts to the network
    # The network is: Alice <--> Bob
    network.add_host(host_alice)
    network.add_host(host_bob)

    # Generate random key
    key_size = 20  # the size of the key in bit
    secret_key = np.random.randint(2, size=key_size)

    # Concatentate functions
    def alice_func(alice):
        msg_buff = []
        alice_qkd(alice, msg_buff, secret_key, host_bob.host_id)
        alice_send_message(alice, secret_key, host_bob.host_id)

    def bob_func(eve):
        msg_buff = []
        eve_key = eve_qkd(eve, msg_buff, key_size, host_alice.host_id)
        eve_receive_message(eve, msg_buff, eve_key, host_alice.host_id)

    # Run Bob and Alice

    t1 = host_alice.run_protocol(alice_func, ())
    t2 = host_bob.run_protocol(bob_func, ())

    t1.join()
    t2.join()

    network.stop(True)


if __name__ == '__main__':
    main()
