import numpy as np

from objects.qubit import Qubit
from components.host import Host
from components.network import Network
from backends.eqsn_backend import EQSNBackend


def quantum_coin_flipping(host, m, n, partner_id, rot_angle):
    """
    Quantum Coin Flipping Protocol.

    Own random variables are b_j and d_ij.
    Partners random variables are a_j and c_ij.

    Own shared: f_ij = b_j ^ d_ij
    Partner shared: e_ij = a_j ^ c_ij

    final own: B = ^b_j for all j
    final partner: A_tilde = ^a_j for all j

    final random bit: A_tilde ^ B
    """
    b = np.random.randint(0, 1, m, dtype=int)
    d = np.random.randint(0, 1, (n, m), dtype=int)

    a = np.zeros(m, dtype=int)

    # qubits received by partner
    partner_qubits = np.ndarray(shape=(n, m, 2), dtype=Qubit)

    # qubits which are in the end at host
    final_qubits = np.ndarray(shape=(n, m, 2), dtype=Qubit)

    for i in range(n):
        for j in range(m):
            q1 = Qubit(host)
            q2 = Qubit(host)

            if d[i, j] == 0:
                q1.rx(rot_angle)
                q2.rx(-1.0 * rot_angle)
            else:
                q1.rx(-1.0 * rot_angle)
                q2.rx(rot_angle)

            # send qubits to partner
            host.send_qubit(partner_id, q1, await_ack=True)
            host.send_qubit(partner_id, q2, await_ack=True)

            # get qubit from partner
            partner_q1 = host.get_data_qubit(partner_id)
            partner_q2 = host.get_data_qubit(partner_id)

            partner_qubits[i, j, 0] = partner_q1
            partner_qubits[i, j, 1] = partner_q2

    for i in range(n):
        for j in range(m):
            f_ij = b[i] ^ d[i, j]

            host.send_classical(partner_id, str(f_ij))
            e_ij = host.get_classical(partner_id, wait=10)[0].content
            e_ij = int(e_ij)

            if e_ij == 0:
                host.send_qubit(partner_id, partner_qubits[i, j, 1])
                final_qubits[i, j, 0] = partner_qubits[i, j, 0]
            else:
                host.send_qubit(partner_id, partner_qubits[i, j, 0])
                final_qubits[i, j, 0] = partner_qubits[i, j, 1]

            final_qubits[i, j, 1] = host.get_data_qubit(partner_id, wait=10)

    for j in range(m):
        # Send own encoded basis to partner
        host.send_classical(partner_id, str(b[j]))

        # Get partner base to decode her qubits
        a_j = host.get_classical(partner_id, wait=10)[0].content
        a_j = int(a_j)

        for i in range(n):
            # Meaure in Psi_a basis or Psi_not_a basis
            q = final_qubits[i, j, 0]
            res = -1
            if a_j == 0:
                q.rx(-1.0 * rot_angle)
            else:
                q.rx(rot_angle)

            res = q.measure()
            # Check if all results match the random number
            # partner has shared with us.
            if res != a_j:
                raise ValueError("Cheater!")

        # a_j got accepted
        a[j] = a_j

        for i in range(n):
            q = final_qubits[i, j, 1]
            if 1 - b[j] == 0:
                q.rx(-1.0 * rot_angle)
            else:
                q.rx(rot_angle)
            res = q.measure()
            if res != 0:
                raise ValueError("Cheater!")

    A_tilde = 0
    for j in range(m):
        A_tilde ^= a[j]

    B = 0
    for j in range(m):
        B ^= b[j]

    random_bit = A_tilde ^ B
    print("%s: random bit is %d" % (host.host_id, random_bit))
    return random_bit


def main():
    network = Network.get_instance()

    # backend = ProjectQBackend()
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

    m = 3
    n = 3
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
