import math
import random
from qunetsim.components.host import Host
from qunetsim.qunetsim.components import Network

PLAYS = 20


def alice_classical(alice_host, referee_id):
    """
    Alice's classical strategy.

    Args:
        alice_host:
        referee_id:
    """
    # Here we write the protocol code for a host.
    for i in range(PLAYS):
        _ = alice_host.get_classical(referee_id, seq_num=i, wait=5)
        alice_host.send_classical(referee_id, "0")


def alice_quantum(alice_host, referee_id, bob_id):
    """
    Alice's quantum protocol for the CHSH game.

    Args:
        alice_host (Host): Alice's Host object
        referee_id (str): Referee's Host ID
        bob_id (str): Bob's Host ID (only for accessing shared EPR pairs)
    """
    for i in range(PLAYS):
        referee_message = alice_host.get_classical(referee_id, seq_num=i, wait=5)
        x = int(referee_message.content)
        epr = alice_host.get_epr(bob_id)

        if x == 0:
            res = epr.measure()
            alice_host.send_classical(referee_id, str(res))
        else:
            epr.H()
            res = epr.measure()
            alice_host.send_classical(referee_id, str(res))


def bob_classical(bob_host, referee_id):
    # Here we write the protocol code for another host.
    for i in range(PLAYS):
        _ = bob_host.get_classical(referee_id, seq_num=i, wait=5)
        bob_host.send_classical(referee_id, "0")


def bob_quantum(bob_host, referee_id, alice_id):
    """
       Bob's quantum protocol for the CHSH game.

       Args:
           bob_host (Host): Bob's Host object
           referee_id (str): Referee's Host ID
           alice_id (str): Alice's Host ID (only for accessing shared EPR pairs)
    """

    for i in range(PLAYS):
        referee_message = bob_host.get_classical(referee_id, seq_num=i, wait=5)

        y = int(referee_message.content)
        epr = bob_host.get_epr(alice_id)

        if y == 0:
            epr.ry(-2.0 * math.pi / 8.0)
            res = epr.measure()
            bob_host.send_classical(referee_id, str(res))
        else:
            epr.ry(2.0 * math.pi / 8.0)
            res = epr.measure()
            bob_host.send_classical(referee_id, str(res))


def referee(ref, alice_id, bob_id):
    """
    Referee protocol for CHSH game.
    Args:
        ref (Host): Referee host object
        alice_id (str): Alice's host ID
        bob_id (str): Bob's host ID

    """

    wins = 0
    for i in range(PLAYS):
        x = random.choice([0, 1])
        ref.send_classical(alice_id, str(x))
        y = random.choice([0, 1])
        ref.send_classical(bob_id, str(y))

        alice_response = ref.get_classical(alice_id, seq_num=i, wait=5)
        bob_response = ref.get_classical(bob_id, seq_num=i, wait=5)

        a = int(alice_response.content)
        b = int(bob_response.content)

        print('X, Y, A, B --- %d, %d, %d, %d' % (x, y, a, b))
        if (x & y) == (a ^ b):
            print('Winners!')
            wins += 1
        else:
            print('Losers!')

    print("Win ratio: " + "{0:.2%}".format(1. * wins / PLAYS))


def main():
    network = Network.get_instance()
    network.start()

    host_A = Host('A')
    host_A.add_c_connection('C')
    host_A.delay = 0
    host_A.start()

    host_B = Host('B')
    host_B.add_c_connection('C')
    host_B.delay = 0
    host_B.start()

    host_C = Host('C')
    host_C.add_c_connections(['A', 'B'])
    host_C.delay = 0
    host_C.start()

    network.add_host(host_C)

    # To generate entanglement
    host_A.add_connection('B')
    host_B.add_connection('A')

    network.add_host(host_A)
    network.add_host(host_B)

    # strategy = 'CLASSICAL'
    strategy = 'QUANTUM'

    host_A.delay = 0.0
    host_B.delay = 0.0
    host_C.delay = 0.0

    print('Starting game. Strategy: %s' % strategy)
    if strategy == 'QUANTUM':
        print('Generating initial entanglement...')
        for i in range(PLAYS):
            host_A.send_epr('B', await_ack=True)
            print('created %d EPR pairs' % (i + 1))
        print('Done generating initial entanglement')
    else:
        network.delay = 0.0

    # Remove the connection from Alice and Bob
    host_A.remove_connection('B')
    host_B.remove_connection('A')
    network.update_host(host_A)
    network.update_host(host_B)

    # Play the game classically
    if strategy == 'CLASSICAL':
        host_A.run_protocol(alice_classical, (host_C.host_id,))
        host_B.run_protocol(bob_classical, (host_C.host_id,), )

    # Play the game quantumly
    if strategy == 'QUANTUM':
        host_A.run_protocol(alice_quantum, (host_C.host_id, host_B.host_id))
        host_B.run_protocol(bob_quantum, (host_C.host_id, host_A.host_id))

    host_C.run_protocol(referee, (host_A.host_id, host_B.host_id), blocking=True)

    network.stop(True)


if __name__ == '__main__':
    main()
