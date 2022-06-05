from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
from qunetsim.backends import EQSNBackend

Logger.DISABLED = True
KEY_LENGTH = 100
WAIT_TIME = 10
INTERCEPTION = False

# Basis Declaration
BASIS_ALICE = ['0', '4', '2']   # 0 = RY(0); 4 = RY(pi/4); 2 = RY(pi/2)
BASIS_BOB = ['4', '2', '3']     # 4 = RY(pi/4); 2 = RY(pi/2); 3 = RY(3*pi/4)
##########################################################################


def entangle(host):     # 01 - 10
    q1 = Qubit(host)
    q2 = Qubit(host)
    q1.X()
    q1.H()
    q2.X()
    q1.cnot(q2)
    return q1, q2


def preparation():
    alice_basis = ""
    bob_basis = ""
    for kl in range(KEY_LENGTH):
        alice_basis += random.choice(BASIS_ALICE)
        bob_basis += random.choice(BASIS_BOB)
    # print("Alice basis: {}".format(alice_basis))
    # print("Bob basis: {}".format(bob_basis))
    return alice_basis, bob_basis


def bell_state(alice_decoy_list, bob_decoy_list):
    count_00 = 0
    count_01 = 0
    count_10 = 0
    count_11 = 0
    expectation = []
    for alice_decoy, bob_decoy in zip(alice_decoy_list, bob_decoy_list):
        if len(alice_decoy) == 0 or len(bob_decoy) == 0:
            continue
        else:
            for i in range(0, len(alice_decoy)):
                if alice_decoy[i] == '0' and bob_decoy[i] == '0':
                    count_00 += 1
                if alice_decoy[i] == '0' and bob_decoy[i] == '1':
                    count_01 += 1
                if alice_decoy[i] == '1' and bob_decoy[i] == '0':
                    count_10 += 1
                if alice_decoy[i] == '1' and bob_decoy[i] == '1':
                    count_11 += 1
        total = len(alice_decoy)
        count = count_00 + count_11 - count_01 - count_10
        expectation.append(count / total)   # E(a,b) = (N_00 + N_11 - N_01 - N_10) / N
    print("Estimate: {}".format(expectation))
    result = expectation[0] - expectation[1] + expectation[2] + expectation[3]  # a1b1 - a1b3 + a3b1 + a3b3
    return result


def alice_key_string(alice_bits, alice_basis, bob_basis):   # A1 = 0, A2 = pi/4, A3 = pi/2; B1 = pi/4, B2 = pi/2, B3 = 3*pi/4
    alice_key_decoy = []
    alice_key_decoy_a1b1 = ""
    alice_key_decoy_a1b3 = ""
    alice_key_decoy_a3b1 = ""
    alice_key_decoy_a3b3 = ""

    alice_key_raw_a2b1 = ""
    alice_key_raw_a3b2 = ""
    alice_key_raw = ""
    for i in range(len(alice_bits)):
        if alice_basis[i] == bob_basis[i]:
            alice_key_raw += str(alice_bits[i])
        if alice_basis[i] == '4' and bob_basis[i] == '4':
            alice_key_raw_a2b1 += str(alice_bits[i])
        if alice_basis[i] == '2' and bob_basis[i] == '2':
            alice_key_raw_a3b2 += str(alice_bits[i])

        if alice_basis[i] == '0' and bob_basis[i] == '4':
            alice_key_decoy_a1b1 += str(alice_bits[i])
        if alice_basis[i] == '0' and bob_basis[i] == '3':
            alice_key_decoy_a1b3 += str(alice_bits[i])
        if alice_basis[i] == '2' and bob_basis[i] == '4':
            alice_key_decoy_a3b1 += str(alice_bits[i])
        if alice_basis[i] == '2' and bob_basis[i] == '3':
            alice_key_decoy_a3b3 += str(alice_bits[i])
    print("Alice Key Decoy 0_4 a1b1: {}".format(alice_key_decoy_a1b1))
    print("Alice Key Decoy 0_3 a1b3: {}".format(alice_key_decoy_a1b3))
    print("Alice Key Decoy 2_4 a3b1: {}".format(alice_key_decoy_a3b1))
    print("Alice Key Decoy 2_3 a3b3: {}".format(alice_key_decoy_a3b3))
    alice_key_decoy.append(alice_key_decoy_a1b1)
    alice_key_decoy.append(alice_key_decoy_a1b3)
    alice_key_decoy.append(alice_key_decoy_a3b1)
    alice_key_decoy.append(alice_key_decoy_a3b3)

    print("Alice Key Raw: {}".format(alice_key_raw))
    print("Alice Key Raw 4 a2b1: {}".format(alice_key_raw_a2b1))
    print("Alice Key Raw 2 a3b2: {}".format(alice_key_raw_a3b2))
    return alice_key_decoy, alice_key_raw_a2b1, alice_key_raw_a3b2, alice_key_raw


def bob_key_string(bob_bits, bob_basis, alice_basis):   # A1 = 0, A2 = pi/4, A3 = pi/2; B1 = pi/4, B2 = pi/2, B3 = 3*pi/4
    bob_key_decoy = []
    bob_key_decoy_a1b1 = ""
    bob_key_decoy_a1b3 = ""
    bob_key_decoy_a3b1 = ""
    bob_key_decoy_a3b3 = ""

    bob_key_raw_a2b1 = ""
    bob_key_raw_a3b2 = ""
    bob_key_raw = ""
    for i in range(len(bob_bits)):
        if bob_basis[i] == alice_basis[i]:
            bob_key_raw += str(bob_bits[i])
        if bob_basis[i] == '4' and alice_basis[i] == '4':
            bob_key_raw_a2b1 += str(bob_bits[i])
        if bob_basis[i] == '2' and alice_basis[i] == '2':
            bob_key_raw_a3b2 += str(bob_bits[i])

        if bob_basis[i] == '4' and alice_basis[i] == '0':
            bob_key_decoy_a1b1 += str(bob_bits[i])
        if bob_basis[i] == '3' and alice_basis[i] == '0':
            bob_key_decoy_a1b3 += str(bob_bits[i])
        if bob_basis[i] == '4' and alice_basis[i] == '2':
            bob_key_decoy_a3b1 += str(bob_bits[i])
        if bob_basis[i] == '3' and alice_basis[i] == '2':
            bob_key_decoy_a3b3 += str(bob_bits[i])
    print("Bob Key Decoy 4_0 a1b1: {}".format(bob_key_decoy_a1b1))
    print("Bob Key Decoy 3_0 a1b3: {}".format(bob_key_decoy_a1b3))
    print("Bob Key Decoy 4_2 a3b1: {}".format(bob_key_decoy_a3b1))
    print("Bob Key Decoy 3_2 a3b3: {}".format(bob_key_decoy_a3b3))
    bob_key_decoy.append(bob_key_decoy_a1b1)
    bob_key_decoy.append(bob_key_decoy_a1b3)
    bob_key_decoy.append(bob_key_decoy_a3b1)
    bob_key_decoy.append(bob_key_decoy_a3b3)

    print("Bob Key Raw: {}".format(bob_key_raw))
    print("Bob Key Raw 4 a2b1: {}".format(bob_key_raw_a2b1))
    print("Bob Key Raw 2 a3b2: {}".format(bob_key_raw_a3b2))
    return bob_key_decoy, bob_key_raw_a2b1, bob_key_raw_a3b2, bob_key_raw


def alice(host, receiver, alice_basis):
    alice_measured_bits = ""
    # For Qubit and Basis
    for basis in alice_basis:
        q1, q2 = entangle(host)
        ack_arrived = host.send_qubit(receiver, q2, await_ack=False)
        if ack_arrived:
            if basis == '0':    # 0
                q1.ry(0.0)
                alice_measured_bits += str(q1.measure())
            if basis == '4':    # pi/4
                q1.ry(0.785398)
                alice_measured_bits += str(q1.measure())
            if basis == '2':    # pi/2
                q1.ry(1.5708)
                alice_measured_bits += str(q1.measure())
    print("Alice's measured bits: {}".format(alice_measured_bits))

    # Sending Basis to Bob
    ack_basis_alice = host.send_classical(receiver, alice_basis, await_ack=True)
    if ack_basis_alice is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    # Receiving Basis from Bob
    basis_from_bob = host.get_next_classical(receiver, wait=WAIT_TIME)
    if basis_from_bob is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))

    # For Key
    alice_key_decoy, alice_key_raw_a2b1, alice_key_raw_a3b2, alice_key_raw = alice_key_string(alice_measured_bits, alice_basis, basis_from_bob.content)
    print("Alice Key Decoy: {}".format(alice_key_decoy))

    # For Sending Decoy Key
    alice_brd_ack = host.send_classical(receiver, alice_key_decoy, await_ack=True)
    if alice_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))
    bob_key_decoy = host.get_next_classical(receiver, wait=WAIT_TIME)
    if bob_key_decoy is not None:
        print("{}'s got successfully by {}".format(receiver, host.host_id))
        print("Bob Key Decoy got by Alice: {}".format(bob_key_decoy.content))

    # For Testing CHSH Inequality
    result = bell_state(alice_key_decoy, bob_key_decoy.content)
    print("Result Alice: {}".format(result))
    if 2.0 <= abs(result) < 4:  # nearly equivalent to 2.82
        print("|S| value: {}".format(abs(result)))
    else:
        print("Alice and Bob discard the bits and run again")


def eve_sniffing_quantum(sender, receiver, qubit):
    qubit.measure(non_destructive=True)


def bob(host, receiver, bob_basis):
    bob_measured_bits = ""
    # For Qubit and Basis
    for basis in bob_basis:
        q2 = host.get_qubit(receiver, wait=WAIT_TIME)
        if q2 is not None:
            # Measuring Alice's qubit based on Bob's basis
            if basis == '4':  # pi/4
                q2.ry(0.785398)
                bob_measured_bits += str(q2.measure())
            if basis == '2':  # pi/2
                q2.ry(1.5708)
                bob_measured_bits += str(q2.measure())
            if basis == '3':  # 3*pi/4
                q2.ry(2.35619)
                bob_measured_bits += str(q2.measure())
    print("Bob's measured bits: {}".format(bob_measured_bits))

    # Receiving Basis from Alice
    basis_from_alice = host.get_next_classical(receiver, wait=WAIT_TIME)
    if basis_from_alice is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
    # Sending Basis to Alice
    ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
    if ack_basis_bob is not None:
        print("{}'s basis string successfully sent".format(host.host_id))

    # For sample key indices
    bob_key_decoy, bob_key_raw_a2b1, bob_key_raw_a3b2, bob_key_raw = bob_key_string(bob_measured_bits, bob_basis, basis_from_alice.content)
    print("Bob Key Decoy: {}".format(bob_key_decoy))

    # For Sending Decoy Key
    alice_key_decoy = host.get_next_classical(receiver, wait=WAIT_TIME)
    if alice_key_decoy is not None:
        print("{}'s key got successfully by {}".format(receiver, host.host_id))
        print("Alice Key Decoy got by Bob: {}".format(alice_key_decoy.content))
    bob_brd_ack = host.send_classical(receiver, bob_key_decoy, await_ack=True)
    if bob_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))

    # For Testing CHSH Inequality
    result = bell_state(alice_key_decoy.content, bob_key_decoy)
    print("Result Bob: {}".format(result))
    if 2.0 <= abs(result) < 4.0:  # nearly equivalent to 2.82
        print("|S| value: {}".format(abs(result)))
    else:
        print("Alice and Bob discard the bits and run again")


def main():
    backend = EQSNBackend()
    network = Network.get_instance()
    nodes = ['Alice', 'Eve', 'Bob']
    network.start(nodes)

    host_alice = Host('Alice', backend)
    host_alice.add_connection('Eve')
    host_alice.start()

    host_eve = Host('Eve', backend)
    host_eve.add_connections(['Alice', 'Bob'])
    host_eve.start()

    host_bob = Host('Bob', backend)
    host_bob.add_connection('Eve')
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_eve)
    network.add_host(host_bob)
    # network.draw_classical_network()
    # network.draw_quantum_network()
    network.start()

    alice_basis, bob_basis = preparation()
    print("Alice bases: {}".format(alice_basis))
    print("Bob bases: {}".format(bob_basis))

    if INTERCEPTION:
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

    t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, ))
    t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, ))
    t1.join()
    t2.join()

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
