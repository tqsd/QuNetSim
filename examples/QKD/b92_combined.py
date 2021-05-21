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
INTERCEPTION = False


# Basis Declaration
BASIS = ['Z', 'X']  # |0> = Z-Basis; |+> = X-Basis or |1> = Z-Basis; |-> = X-Basis
##########################################################################


def q_bit(host, encode):
    q = Qubit(host)
    if encode == '+':
        q.H()
    if encode == '0':
        q.I()
    return q


def encoded_bases(alice_bits, alice_basis):     # Can we do some operation on the bits so that it will come to encoded basis ?
    alice_encoded = ""
    for i in range(0, len(alice_bits)):
        if alice_bits[i] == '1':  # X-Basis
            alice_encoded += '+'
        if alice_bits[i] == '0':  # Z-Basis
            alice_encoded += '0'
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


def alice_key_string(alice_bits, indices):
    alice_list = list(alice_bits)
    for i in indices:
        alice_list[int(i)] = '_'
    alice_list = [e for e in alice_list if e != '_']
    alice_key = ''.join(alice_list)
    print("Alice Bits: {}".format(alice_key))
    return alice_key


def bob_key_string(bob_bits):
    bob_list = list(bob_bits)
    bob_list = [e for e in bob_list if e != '_']
    bob_key = ''.join(bob_list)
    print("Bob Bits: {}".format(bob_key))
    return bob_key


def alice(host, receiver, alice_basis, alice_bits, alice_encoded):
    # For Qubit and Basis
    for i, encode in enumerate(alice_encoded):
        _, ack = host.send_qubit(receiver, q_bit(host, encode), await_ack=True)
        if ack is not None:
            print("{}'s qubit {} successfully sent".format(host.host_id, i))

    msg_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
    if msg_from_bob is not None:
        print("Got indices from {}".format(receiver))

    # For Key
    alice_key = alice_key_string(alice_bits, msg_from_bob[0].content)


def eve_sniffing_quantum(sender, receiver, qubit):
    qubit.measure(non_destructive=True)


def bob(host, receiver, bob_basis):
    indices = []
    bob_key = ""
    bob_measured_bits = ""
    # For Qubit and Basis
    for i in range(0, len(bob_basis)):
        data = host.get_data_qubit(receiver, wait=WAIT_TIME)
        if data is not None:
            print("{}'s qubit {} got successfully by {}".format(receiver, i, host.host_id))
        # Measuring Alice's qubit based on Bob's basis
        if bob_basis[i] == 'Z':  # Z-basis; 0
            res = data.measure()
            if res == 1:
                bob_measured_bits += str(res)
            else:
                indices.append(str(i))
                bob_measured_bits += '_'
        if bob_basis[i] == 'X':  # X-basis; +
            data.H()
            data.X()
            res = data.measure()
            if res == 0:
                bob_measured_bits += str(res)
            else:
                indices.append(str(i))
                bob_measured_bits += '_'

    print("Bob measured bit: {}".format(bob_measured_bits))
    print(indices)

    # Sending indices to Alice
    msg_to_alice = host.send_classical(receiver, indices, await_ack=True)
    if msg_to_alice is not None:
        print("Indices sent to {}".format(receiver))

    # For sample key indices
    bob_key = bob_key_string(bob_measured_bits)


def main():
    network = Network.get_instance()
    nodes = ['Alice', 'Eve', 'Bob']
    network.start(nodes)
    network.delay = 0.1

    host_alice = Host('Alice')
    host_alice.add_connection('Eve')
    host_alice.start()

    host_eve = Host('Eve')
    host_eve.add_connections(['Alice', 'Bob'])
    host_eve.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Eve')
    host_bob.delay = 0.2
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_eve)
    network.add_host(host_bob)
    # network.draw_classical_network()
    # network.draw_quantum_network()
    network.start()

    alice_basis, bob_basis, alice_bits, alice_encoded = preparation()
    print("Alice bases: {}".format(alice_basis))
    print("Bob bases: {}".format(bob_basis))
    print("Alice bits: {}".format(alice_bits))
    print("Alice encoded: {}".format(alice_encoded))

    if INTERCEPTION:
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

    t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, alice_bits, alice_encoded, ))
    t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, ))
    t1.join()
    t2.join()

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
