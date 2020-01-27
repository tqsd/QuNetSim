CHSH Game
----------------

In this example, we show how to play the CHSH game with QuNetSim. The CHSH game is an example where
a quantum strategy outperforms or wins more often, than any classical strategy. In the game, there are three parties.
A referee and two cooperating players, Alice and Bob. The point of the game is, the referee sends Alice and Bob each
a random bit, :math:`x` to Alice and :math:`y` to Bob, that is, with probability :math:`0.5` Alice and Bob will receive a :math:`0` and with :math:`0.5` a :math:`1`.
During the game, Alice and Bob cannot communicate with each other, but to win the game they each have to send a bit back to
the referee such that the equation :math:`x` **and**  :math:`y = a` **xor**  :math:`b`, where :math:`a` and :math:`b` are the bits Alice and Bob send to the referee.

Before the game, Alice and Bob can devise a strategy and distribute resources that they can use during the game, as long as the resource is not a method of communication. The optical strategy for winning the game classically is that no matter
what the referee sends them, Alice and Bob both send a math:`0`. With this strategy, they can win :math:`75\%` of the time. If they instead use a quantum strategy, before the game starts, they can distribute amongst themselves entangled pairs
of qubits. Then, depending on the bit that the referee sends then, they perform  a specific measurement on their half of the
qubits. With this strategy, they can win roughly :math:`85\%` of the time.

Below, we play the game both classically and quantumly.

The protocol that the referee runs the following. The referee simply generates 2 random bits and sends them
to Alice and Bob respectively. He then awaits a response from both Alice and Bob and then records the statistics
for if Alice and Bob won or lost.

..  code-block:: python
    :linenos:

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
            if x & y == a ^ b:
                print('Winners!')
                wins += 1
            else:
                print('Losers!')

        print("Win ratio: " + "{0:.2%}".format(1. * wins / PLAYS))



Next we see Alice's protocols for the classical and quantum strategies. In the classical strategy, she simply awaits
a message from the referee and then sends back a 0 in all cases.

Quantumly, when she receives the message from the referee, she performs either a :math:`Z` basis measurement or
and :math:`X` basis.


..  code-block:: python
    :linenos:

     def alice_classical(alice_host, referee_id):
        """
        Alice's classical protocol for the CHSH game.

        Args:
            alice_host (Host): Alice's Host object
            referee_id (str): Referee's Host ID
        """
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


Classically, Bob does uses the exact same strategy. Quantumly Bob has a similar approach except that he uses another basis for his measurements, namely a rotated basis in the Y-axis.

..  code-block:: python
    :linenos:


    def bob_classical(bob_host, referee_id):
        """
        Bob's classical protocol for the CHSH game.

        Args:
            bob_host (Host): Bob's Host object
            referee_id (str): Referee's Host ID
        """
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


For this example, because we are using rotation operators, we need to change the system backend to one that supports
such operations. QuNetSim supports, at the moment, three backends for qubits, namely, SimulaQron, ProjectQ, and a
qubit simulator that we've developed called ESQN. ProjectQ and EQSN both support rotation operators and so we use either
of those here. The full example is below, with the backends imported and set.

..  code-block:: python
    :linenos:

    import math
    import random
    from components.host import Host
    from components.network import Network
    from components.logger import Logger

    # We have to import the ProjectQ backend.
    # One  should ensure the python library "projectq" is installed.
    from backends.projectq_backend import ProjectQBackend

    # Disable QuNetSim logging
    Logger.DISABLED = True

    # Number of times to play the game.
    PLAYS = 20

    # Classical or Quantum strategy for the game
    # strategy = 'CLASSICAL'
    strategy = 'QUANTUM'


    def alice_classical(alice_host, referee_id):
        """
        Alice's classical protocol for the CHSH game.

        Args:
            alice_host (Host): Alice's Host object
            referee_id (str): Referee's Host ID
        """
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
        """
        Bob's classical protocol for the CHSH game.

        Args:
            bob_host (Host): Bob's Host object
            referee_id (str): Referee's Host ID
        """
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
            if x & y == a ^ b:
                print('Winners!')
                wins += 1
            else:
                print('Losers!')

        print("Win ratio: %.2f" % (100. * wins / PLAYS))


    def main():
        network = Network.get_instance()
        backend = ProjectQBackend()
        nodes = ['A', 'B', 'C']
        network.delay = 0.1
        network.start(nodes, backend)

        host_A = Host('A', backend)
        host_A.add_c_connection('C')
        host_A.start()

        host_B = Host('B', backend)
        host_B.add_c_connection('C')
        host_B.start()

        host_C = Host('C', backend)
        host_C.add_c_connection('A')
        host_C.add_c_connection('B')
        host_C.start()

        network.add_host(host_C)

        # For entanglement generation
        host_A.add_connection('B')
        host_B.add_connection('A')

        network.add_host(host_A)
        network.add_host(host_B)

        if strategy == 'QUANTUM':
            print('Generating initial entanglement')
            for i in range(PLAYS):
                host_A.send_epr('B', await_ack=True)
            print('Done generating initial entanglement')

        # Remove the connection from Alice and Bob
        host_A.remove_connection('B')
        host_B.remove_connection('A')
        network.update_host(host_A)
        network.update_host(host_B)

        print('Starting game. Strategy: %s' % strategy)

        # Play the game classically
        if strategy == 'CLASSICAL':
            host_A.run_protocol(alice_classical, (host_C.host_id,))
            host_B.run_protocol(bob_classical, (host_C.host_id,), )

        # Play the game quantumly
        if strategy == 'QUANTUM':
            host_A.run_protocol(alice_quantum, (host_C.host_id, host_B.host_id))
            host_B.run_protocol(bob_quantum, (host_C.host_id, host_A.host_id))

        host_C.run_protocol(referee, (host_A.host_id, host_B.host_id), blocking=True)


    if __name__ == '__main__':
        main()
