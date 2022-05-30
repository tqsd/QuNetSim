from qunetsim import Qubit
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random

Logger.DISABLED = True
KEY_LENGTH = 50
SAMPLE_SIZE = int(KEY_LENGTH / 4)
WAIT_TIME = 60


# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
##########################################################################


def q_bit(host, encode):
    q = Qubit(host)
    if encode == '+':
        q.H()
    if encode == '-':
        q.X()
        q.H()
    if encode == '0':
        q.I()
    if encode == '1':
        q.X()
    return q


def encoded_bases(alice_bits, alice_basis):     # Can we do some operation on the bits so that it will come to encoded basis ?
    alice_encoded = ""
    for i in range(0, len(alice_bits)):
        if alice_basis[i] == 'X':  # X-Basis
            if alice_bits[i] == '0':
                alice_encoded += '+'
            if alice_bits[i] == '1':
                alice_encoded += '-'
        if alice_basis[i] == 'Z':  # Z-Basis
            if alice_bits[i] == '0':
                alice_encoded += '0'
            if alice_bits[i] == '1':
                alice_encoded += '1'
    # print("Alice encoded: {}".format(alice_encoded))
    return alice_encoded


def preparation():
    alice_basis = ""
    bob_basis = ""
    alice_bits = ""
    for kl in range(KEY_LENGTH):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
        alice_bits += str(random.getrandbits(1))
    # print("Alice basis: {}".format(alice_basis))
    # print("Bob basis: {}".format(bob_basis))
    # print("Alice bits: {}".format(alice_bits))
    alice_encoded = encoded_bases(alice_bits, alice_basis)
    return alice_basis, bob_basis, alice_bits, alice_encoded


def alice_key_string(alice_bits, alice_basis, bob_basis):
    alice_key = ""
    for i in range(SAMPLE_SIZE):
        if alice_basis[i] == bob_basis[i]:
            alice_key += str(alice_bits[int(i)])
    print("Alice Key: {}".format(alice_key))
    return alice_key


def bob_key_string(bob_bits, bob_basis, alice_basis):
    bob_key = ""
    for i in range(SAMPLE_SIZE):
        if bob_basis[i] == alice_basis[i]:
            bob_key += str(bob_bits[i])
    print("Bob Key: {}".format(bob_key))
    return bob_key


def alice(host, receiver, alice_basis, alice_bits, alice_encoded):
    # For Qubit and Basis
    for i, encode in enumerate(alice_encoded):
        _, ack = host.send_qubit(receiver, q_bit(host, encode), await_ack=True)
        if ack is not None:
            print("{}'s qubit {} successfully sent".format(host.host_id, i))

    # Sending Basis to Bob
    ack_basis_alice = host.send_classical(receiver, alice_basis, await_ack=True)
    if ack_basis_alice is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    # Receiving Basis from Bob
    basis_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_bob is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))

    # For Key
    alice_key = alice_key_string(alice_bits, alice_basis, basis_from_bob[0].content)

    # For Sending Key
    alice_brd_ack = host.send_classical(receiver, alice_key, await_ack=True)
    if alice_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))
    bob_key = host.get_classical(receiver, wait=WAIT_TIME)
    if bob_key is not None:
        print("{}'s got successfully by {}".format(receiver, host.host_id))
        if alice_key == bob_key[0].content:
            print("Same key from {}'s side".format(host.host_id))


def bob(host, receiver, bob_basis):
    bob_key = ""
    bob_measured_bits = ""
    # For Qubit and Basis
    for i in range(0, len(bob_basis)):
        data = host.get_qubit(receiver, wait=WAIT_TIME)
        if data is not None:
            print("{}'s qubit {} got successfully by {}".format(receiver, i, host.host_id))
        # Measuring Alice's qubit based on Bob's basis
        if bob_basis[i] == 'Z':  # Z-basis
            bob_measured_bits += str(data.measure())
        if bob_basis[i] == 'X':  # X-basis
            data.H()
            bob_measured_bits += str(data.measure())
    print("Bob measured bit: {}".format(bob_measured_bits))

    # Receiving Basis from Alice
    basis_from_alice = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_alice is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
    # Sending Basis to Alice
    ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
    if ack_basis_bob is not None:
        print("{}'s basis string successfully sent".format(host.host_id))

    # For sample key indices
    bob_key = bob_key_string(bob_measured_bits, bob_basis, basis_from_alice[0].content)

    # For Broadcast Key
    alice_key = host.get_classical(receiver, wait=WAIT_TIME)
    if alice_key is not None:
        print("{}'s key got successfully by {}".format(receiver, host.host_id))
        if bob_key == alice_key[0].content:
            print("Same key from {}'s side".format(host.host_id))
    bob_brd_ack = host.send_classical(receiver, bob_key, await_ack=True)
    if bob_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))


def main():
    network = Network.get_instance()
    nodes = ['Alice', 'Eve', 'Bob']
    network.start(nodes)

    host_alice = Host('Alice')
    host_alice.add_connection('Eve')
    host_alice.start()

    host_eve = Host('Eve')
    host_eve.add_connections(['Alice', 'Bob'])
    host_eve.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Eve')
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_eve)
    network.add_host(host_bob)
    network.draw_classical_network()
    network.draw_quantum_network()
    network.start()

    alice_basis, bob_basis, alice_bits, alice_encoded = preparation()
    print("Alice bases: {}".format(alice_basis))
    print("Bob bases: {}".format(bob_basis))
    print("Alice bits: {}".format(alice_bits))
    print("Alice encoded: {}".format(alice_encoded))

    t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, alice_bits, alice_encoded, ))
    t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, ))
    t1.join()
    t2.join()

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
