from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.daemon_thread import DaemonThread
from components import protocols


def qudp_sender(host, q_size, receiver_id):
    bit_arr = np.random.randint(2, size=q_size)
    print(bit_arr)
    data_qubits = []

    checksum_size = 2
    checksum_per_qubit = int(q_size / checksum_size)

    for i in range(q_size):
        q_tmp = qubit(host.cqc)
        if bit_arr[i] == 1:
            q_tmp.X()
        data_qubits.append(q_tmp)

    checksum_qubits = protocols._add_checksum(host.cqc, data_qubits, checksum_per_qubit)
    data_qubits.extend(checksum_qubits)
    host.send_classical(receiver_id, checksum_size, await_ack=False)

    # Pre-generate EPR pairs
    # epr_array = []
    # for i in range(len(data_qubits)):
    #     id = host.send_epr(receiver_id, await_ack=False)
    #     epr_array.append(host.get_epr(receiver_id, id))

    print(len(data_qubits))
    for q in data_qubits:
        host.send_teleport(receiver_id, q, await_ack=False)
    print('out of loop')


def qudp_receiver(host, q_size, sender_id):
    wait_time = 10
    messages = host.get_classical(sender_id, wait=wait_time)

    assert messages is not None and len(messages) > 0

    checksum_size = int(messages[0]['message'])
    checksum_per_qubit = int(q_size / checksum_size)

    wait = 50
    wait_start_time = time.time()
    # TODO: Let's modify get_data_qubits so that it can wait t seconds for n qubits
    while (time.time() - wait_start_time < wait):
        if len(host.get_data_qubits(sender_id)) == (q_size + checksum_size):
            break

    if len(host.get_data_qubits(sender_id)) != q_size + checksum_size:
        print('data qubits did not arrive')
        return
    else:
        print('qubits arrived')

    # for i in range(len(host.get_data_qubits(sender_id))):
    #     q = host.get_data_qubit(sender_id,wait = 3)
    #     print('q measurement')
    #     print(q['q'].measure())

    # print('checksum qubit')
    # print(host.get_data_qubit(sender_id)['q'].measure())

    print('length of data qubits')
    print(len(host.get_data_qubits(sender_id)))

    # print('data_qubits')
    # print( host.get_data_qubits(sender_id)[::-1])
    data_qubits = host.get_data_qubits(sender_id)

    print('data qubits')
    print(data_qubits)

    checksum_qubits = []
    checksum_cnt = 0
    for i in range(len(host.get_data_qubits(sender_id))):
        if checksum_cnt < checksum_size:
            checksum_qubits.append(data_qubits[q_size + i]['q'])
            checksum_cnt = checksum_cnt + 1

    k = 1
    for i in range(len(data_qubits) - checksum_size):
        data_qubits[i]['q'].cnot(checksum_qubits[k - 1])
        if i == (k * checksum_per_qubit - 1):
            k = k + 1

    for i in range(len(checksum_qubits)):
        if checksum_qubits[i].measure() != 0:
            print('Error exists in UDP packet')

    print('No error exist in UDP packet')

    rec_bits = []
    for i in range(len(data_qubits) - checksum_size):
        rec_bits.append(data_qubits[i]['q'].measure())

    print('rec_bits')
    print(rec_bits)
    return


def main():
    network = Network.get_instance()

    nodes = ["Alice", "Bob"]
    network.start(nodes)

    network.delay = 0.5
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:
        host_alice = Host('alice', Alice)
        host_alice.add_connection('bob')
        host_alice.add_c_connection('eve')
        host_alice.max_ack_wait = 10
        host_alice.delay = 0.2
        host_alice.start()

        host_bob = Host('bob', Bob)
        host_bob.max_ack_wait = 10
        host_bob.delay = 0.2
        host_bob.add_connection('alice')
        host_bob.add_q_connection('dean')
        host_bob.start()

        network.add_host(host_alice)
        network.add_host(host_bob)

        q_size = 6

        DaemonThread(qudp_sender, args=(host_alice, q_size, host_bob.host_id))
        DaemonThread(qudp_receiver, args=(host_bob, q_size, host_alice.host_id))

        start_time = time.time()
        while time.time() - start_time < 50:
            pass

        network.stop(stop_hosts=True)


if __name__ == '__main__':
    main()
