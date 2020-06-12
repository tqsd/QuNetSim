Quantum Coin Flipping
------------------------

This example implements the Quantum Coin Flipping protocol.
A detailed description can be found
`here <https://arxiv.org/abs/quant-ph/9904078>`__ and
a description about
its implementation is briefly summarized
`here <https://wiki.veriqloud.fr/index.php?title=Quantum_Coin_Flipping>`__.

We chose the two quantum states needed for the protocol as

* :math:`\Psi = c |0\rangle + s |1\rangle`
* :math:`\Psi = c |0\rangle - s |1\rangle`

where

* :math:`c = \Re(e^{i \theta})`
* :math:`s = \Im(e^{i \theta})`

and Θ can be chosen. It is suggested that :math:`\theta = \frac{\pi}{9}`.

For the implementation of the protocol, first, we allocate all variables
we need during the protocol. They consist of:

* The hosts own random bits, :math:`b_j` and :math:`d_ij`
* The random bits of the partner host, :math:`a_j`
* The qubits from the partner, :math:`\Psi_{e_{ij}}` and :math:`\Psi_{\bar{e}_{ij}}`
* The final sorted qubits which are left at the end of the protocol in this host, :math:`\Psi_{a_j}` and :math:`\Psi_{\bar{b}_{j}}`

..  code-block:: python
    :linenos:

    # own random bits
    random_bits_b = np.random.randint(0, 2, m, dtype=int)
    random_bits_d = np.random.randint(0, 2, (n, m), dtype=int)

    # random bits received from partner
    random_bits_a = np.zeros(m, dtype=int)

    # qubits received by partner
    # Qubits are Ψ_e_ij and Ψ_e_ij_bar
    partner_qubits = np.ndarray(shape=(n, m, 2), dtype=Qubit)

    # Qubits which are at the end of the protocol
    # at this host. First index determines the state,
    # Ψ_a_j and Ψ_b_j_bar, where the second index (1,...,m)
    # should be m copies of this state.
    psi_a = np.ndarray(shape=(n, m), dtype=Qubit)
    psi_b_bar = np.ndarray(shape=(n, m), dtype=Qubit)

In the first step, for every random number :math:`d_{ij}`,
two qubits are prepared; The first in the state :math:`\Psi_{d_{ij}}` and the second
in the state :math:`\Psi_{\bar{d}_{ij}}`. This two states are send
to the partner. The states of the partner, from his random bits, are
received and stored in *partner_qubits*.

..  code-block:: python
    :linenos:

    for i in range(n):
        for j in range(m):
            q1 = Qubit(host)
            q2 = Qubit(host)

            # Generate q1 as Ψ_d and
            # q2 as Ψ_d_bar
            if random_bits_d[i, j] == 0:
                # q1 is Ψ_0
                q1.rx(rot_angle)
                # q2 is Ψ_1
                q2.rx(-1.0 * rot_angle)
            else:
                # q1 is Ψ_1
                q1.rx(-1.0 * rot_angle)
                # q2 is Ψ_0
                q2.rx(rot_angle)

            # send and get q1 from our partner
            host.send_qubit(partner_id, q1, await_ack=True)
            partner_q1 = host.get_data_qubit(partner_id)

            # send and get q2 from our partner
            host.send_qubit(partner_id, q2, await_ack=True)
            partner_q2 = host.get_data_qubit(partner_id)

            partner_qubits[i, j, 0] = partner_q1
            partner_qubits[i, j, 1] = partner_q2

In the second step, a new bit, :math:`f_{ij}`, is generated from the random bits generated
in the beginning. This bit is send to the partner and determines which of
the two quantum states, which
have been send to the partner earlier, is in the state :math:`\Psi_{b_j}`.
However, the partner only knows if it is the first or second of the qubits
received, but does not gain any information about the random variable :math:`b_j`.
The partner returns the qubit in the state :math:`\Psi_{\bar{b}_j}`.
The partner also generates such a bit, :math:`e_{ij}`,
and the host returns the quantum state :math:`\Psi_{\bar{a}_j}`.

..  code-block:: python
    :linenos:

    for i in range(n):
        for j in range(m):
            # random bit generated from own two random bits
            f_ij = random_bits_b[j] ^ random_bits_d[i, j]

            # give partner information about this two bits
            host.send_classical(partner_id, str(f_ij))

            # get the partners generated bit of his two
            # random bits by a XOR operation
            msg = host.get_next_classical(partner_id)
            e_ij = int(msg.content)

            # dependent on this bit, send him one of the
            # qubits received. The other qubit should be
            # in the state Ψ_a_j.
            if e_ij == 0:
                host.send_qubit(partner_id, partner_qubits[i, j, 1])
                psi_a[i, j] = partner_qubits[i, j, 0]
            else:
                host.send_qubit(partner_id, partner_qubits[i, j, 0])
                psi_a[i, j] = partner_qubits[i, j, 1]

            # The partner should send the qubit Ψ_b_j_bar back.
            psi_b_bar[i, j] = host.get_data_qubit(partner_id, wait=10)

After this procedure, the host has m qubits of the state
:math:`\Psi_{\bar{b}_j}` and m qubits of :math:`\Psi_{a_j}`, for all j.
If one of the two partners of the protocol want to cheat and manipulate
the outcome of the final random bit, they first have to know the numbers chosen
by their partner.
However, at this point the host has a stack of quantum states from the chosen
numbers of his partner, making it impossible for the partner to change its prior chosen
numbers.
Therefore, the two partners can now start to share their chosen random
numbers and measure their stack of qubits to verify the numbers haven't been tampered with.


..  code-block:: python
    :linenos:

    for j in range(m):
        # Send own random bits b_j to partner
        host.send_classical(partner_id, str(random_bits_b[j]))

        # Get partner base to decode her qubits
        msg = host.get_next_classical(partner_id)
        a_j = int(msg.content)

        for i in range(n):
            # Meaure in Psi_0 basis or Psi_1 basis
            # Because Partner has to tell us the right basis,
            # our measurement outcome should always be 0.
            q = psi_a[i, j]
            res = -1
            if a_j == 0:
                q.rx(-1.0 * rot_angle)
            else:
                q.rx(rot_angle)

            res = q.measure()
            # Check if all results match the random number
            # partner has shared with us.
            if res != 0:
                raise ValueError("Cheater!")

        # a_j got accepted
        random_bits_a[j] = a_j

        # Check if returned psi_b_bar is valid
        # or if partner has measured it to gain information
        # about b.
        for i in range(n):
            q = psi_b_bar[i, j]
            if 1 - random_bits_b[j] == 0:
                q.rx(-1.0 * rot_angle)
            else:
                q.rx(rot_angle)
            res = q.measure()
            if res != 0:
                raise ValueError("Cheater!")


In the last step, the final random number on which both partners can
agree on is generated. The final random number is :math:`\left(\oplus_j a_j\right) \oplus \left(\oplus_j b_j\right)`.


..  code-block:: python
    :linenos:

    # random number generated by singe random numbers
    # of partner
    randomnes_from_partner = 0
    for j in range(m):
        randomnes_from_partner ^= random_bits_a[j]

    # random number generated by own single random numbers
    own_randomnes = 0
    for j in range(m):
        own_randomnes ^= random_bits_b[j]

    # concatenation of both random numbers
    random_bit = randomnes_from_partner ^ own_randomnes
    print("%s: random bit is %d" % (host.host_id, random_bit))
    return random_bit

The full example is given below.

.. code-block:: python
   :linenos:

    import numpy as np

    from qunetsim.objects import Qubit
    from qunetsim.components.host import Host
    from qunetsim.components.network import Network
    from qunetsim.backends.eqsn_backend import EQSNBackend
    # from qunetsim.backends.cqc_backend import CQCBackend
    # from qunetsim.backends.projectq_backend import ProjectQBackend


    def quantum_coin_flipping(host, m, n, partner_id, rot_angle):
        """
        Quantum Coin Flipping Protocol.
        see https://arxiv.org/abs/quant-ph/9904078
        or https://wiki.veriqloud.fr/index.php?title=Quantum_Coin_Flipping

        The two quantum states we use are:
        Ψ_0 = c |0> + s |1>
        Ψ_1 = c |0> - s |1>
        where
        c = Re{e^(iΘ)}
        s = Im{e^(iΘ)}
        and Θ is given by the rot_angle.

        Own random bits are b_j and d_ij.
        Partners random variables are a_j and c_ij.

        Own shared: f_ij = b_j ^ d_ij
        Partner shared: e_ij = a_j ^ c_ij

        final own: B = ^b_j for all j
        final partner: A_tilde = ^a_j for all j

        final random bit: A_tilde ^ B
        """
        # own random bits
        random_bits_b = np.random.randint(0, 2, m, dtype=int)
        random_bits_d = np.random.randint(0, 2, (n, m), dtype=int)

        # random bits received from partner
        random_bits_a = np.zeros(m, dtype=int)

        # qubits received by partner
        # Qubits are Ψ_e_ij and Ψ_e_ij_bar
        partner_qubits = np.ndarray(shape=(n, m, 2), dtype=Qubit)

        # Qubits which are at the end of the protocol
        # at this host. First index determines the state,
        # Ψ_a_j and Ψ_b_j_bar, where the second index (1,...,m)
        # should be m copies of this state.
        psi_a = np.ndarray(shape=(n, m), dtype=Qubit)
        psi_b_bar = np.ndarray(shape=(n, m), dtype=Qubit)

        for i in range(n):
            for j in range(m):
                q1 = Qubit(host)
                q2 = Qubit(host)

                # Generate q1 as Ψ_d and
                # q2 as Ψ_d_bar
                if random_bits_d[i, j] == 0:
                    # q1 is Ψ_0
                    q1.rx(rot_angle)
                    # q2 is Ψ_1
                    q2.rx(-1.0 * rot_angle)
                else:
                    # q1 is Ψ_1
                    q1.rx(-1.0 * rot_angle)
                    # q2 is Ψ_0
                    q2.rx(rot_angle)

                # send and get q1 from our partner
                host.send_qubit(partner_id, q1, await_ack=True)
                partner_q1 = host.get_data_qubit(partner_id)

                # send and get q2 from our partner
                host.send_qubit(partner_id, q2, await_ack=True)
                partner_q2 = host.get_data_qubit(partner_id)

                partner_qubits[i, j, 0] = partner_q1
                partner_qubits[i, j, 1] = partner_q2

        for i in range(n):
            for j in range(m):
                # random bit generated from own two random bits
                f_ij = random_bits_b[j] ^ random_bits_d[i, j]

                # give partner information about this two bits
                host.send_classical(partner_id, str(f_ij))

                # get the partners generated bit of his two
                # random bits by a XOR operation
                msg = host.get_next_classical(partner_id)
                e_ij = int(msg.content)

                # dependent on this bit, send him one of the
                # qubits received. The other qubit should be
                # in the state Ψ_a_j.
                if e_ij == 0:
                    host.send_qubit(partner_id, partner_qubits[i, j, 1])
                    psi_a[i, j] = partner_qubits[i, j, 0]
                else:
                    host.send_qubit(partner_id, partner_qubits[i, j, 0])
                    psi_a[i, j] = partner_qubits[i, j, 1]

                # The partner should send the qubit Ψ_b_j_bar back.
                psi_b_bar[i, j] = host.get_data_qubit(partner_id, wait=10)

        for j in range(m):
            # Send own random bits b_j to partner
            host.send_classical(partner_id, str(random_bits_b[j]))

            # Get partner base to decode her qubits
            msg = host.get_next_classical(partner_id)
            a_j = int(msg.content)

            for i in range(n):
                # Meaure in Psi_0 basis or Psi_1 basis
                # Because Partner has to tell us the right basis,
                # our measurement outcome should always be 0.
                q = psi_a[i, j]
                res = -1
                if a_j == 0:
                    q.rx(-1.0 * rot_angle)
                else:
                    q.rx(rot_angle)

                res = q.measure()
                # Check if all results match the random number
                # partner has shared with us.
                if res != 0:
                    raise ValueError("Cheater!")

            # a_j got accepted
            random_bits_a[j] = a_j

            # Check if returned psi_b_bar is valid
            for i in range(n):
                q = psi_b_bar[i, j]
                if 1 - random_bits_b[j] == 0:
                    q.rx(-1.0 * rot_angle)
                else:
                    q.rx(rot_angle)
                res = q.measure()
                if res != 0:
                    raise ValueError("Cheater!")

        # random number generated by singe random numbers
        # of partner
        randomnes_from_partner = 0
        for j in range(m):
            randomnes_from_partner ^= random_bits_a[j]

        # random number generated by own single random numbers
        own_randomnes = 0
        for j in range(m):
            own_randomnes ^= random_bits_b[j]

        # concatenation of both random numbers
        random_bit = randomnes_from_partner ^ own_randomnes
        print("%s: random bit is %d" % (host.host_id, random_bit))
        return random_bit


    def main():
        network = Network.get_instance()

        # backend = ProjectQBackend()
        # backend = CQCBackend()
        backend = EQSNBackend()

        nodes = ['A', 'B']
        network.delay = 0.1
        network.start(nodes, backend)

        host_A = Host('A', backend)
        host_A.add_connection('B')
        host_A.delay = 0
        host_A.start()

        host_B = Host('B', backend)
        host_B.add_connection('A')
        host_B.delay = 0
        host_B.start()

        network.add_host(host_A)
        network.add_host(host_B)

        m = 2
        n = 4
        rot_angle = np.pi/9

        t1 = host_A.run_protocol(quantum_coin_flipping,
                                arguments=(m, n, host_B.host_id, rot_angle))
        t2 = host_B.run_protocol(quantum_coin_flipping,
                                arguments=(m, n, host_A.host_id, rot_angle))

        t1.join()
        t2.join()

        network.stop(True)

        if __name__ == "__main__":
            main()
