Quantum Coin Flipping
------------------------

This example implements the Quantum Coin Flipping protocol.
A detailed description of is shown
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

and Θ can be chosen customly.

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
two qubits are prepared; The first in the state :math:`\Psi_{d_{ij}}}` and the second
in the state :math:`\Psi_{\bar{d}_{ij}}`. This two states are send
to the partner, and from the partner these states, of his random bits, are
also received and stored in *partner_qubits*.

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
