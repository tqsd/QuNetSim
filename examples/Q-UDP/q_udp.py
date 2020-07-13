import time
import numpy as np

from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger

Logger.DISABLED = False

def qudp_sender(host, q_size, receiver_id):
    bit_arr = np.random.randint(2, size=q_size)
    data_qubits = []

    checksum_size = 3
    checksum_per_qubit = int(q_size / checksum_size)

    print('---------')
    print('Sender sends the classical bits: ' + str(bit_arr))
    print('---------')

    for i in range(q_size):
        q_tmp = Qubit(host)
        if bit_arr[i] == 1:
            q_tmp.X()
        data_qubits.append(q_tmp)

    checksum_qubits = host.add_checksum(data_qubits, checksum_per_qubit)
    data_qubits.extend(checksum_qubits)
    host.send_classical(receiver_id, checksum_size, await_ack=False)

    for q in data_qubits:
        host.send_qubit(receiver_id, q, await_ack=False)


def qudp_receiver(host, q_size, sender_id):
    wait_time = 10
    messages = host.get_classical(sender_id, wait=wait_time)

    assert messages is not None and len(messages) > 0

    checksum_size = int(messages[0].content)
    checksum_per_qubit = int(q_size / checksum_size)

    wait_start_time = time.time()

    # TODO: Let's modify get_data_qubits so that it can wait t seconds for n qubits
    while time.time() - wait_start_time < wait_time * q_size:
        if len(host.get_data_qubits(sender_id)) == (q_size + checksum_size):
            break

    if len(host.get_data_qubits(sender_id)) != q_size + checksum_size:
        print('data qubits did not arrive')
        return
    else:
        print('qubits arrived')

    data_qubits = host.get_data_qubits(sender_id)

    checksum_qubits = []
    checksum_cnt = 0
    for i in range(len(host.get_data_qubits(sender_id))):
        if checksum_cnt < checksum_size:
            checksum_qubits.append(data_qubits[q_size + i].qubit)
            checksum_cnt = checksum_cnt + 1

    k = 1
    for i in range(len(data_qubits) - checksum_size):
        data_qubits[i].qubit.cnot(checksum_qubits[k - 1])
        if i == (k * checksum_per_qubit - 1):
            k = k + 1

    errors = 0
    for i in range(len(checksum_qubits)):
        if checksum_qubits[i].measure() != 0:
            errors += 1

    print('---------')
    if errors == 0:
        print('No error exist in UDP packet')
    else:
        print('There were errors in the UDP transmission')
    print('---------')

    rec_bits = []
    for i in range(len(data_qubits) - checksum_size):
        rec_bits.append(data_qubits[i].qubit.measure())

    print('---------')
    print('Receiver received the classical bits: ' + str(rec_bits))
    print('---------')

    return


def main():
    network = Network.get_instance()

    nodes = ["Alice", "Bob"]
    network.x_error_rate = 0
    network.delay = 0.5
    network.start(nodes)

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.max_ack_wait = 10
    host_alice.delay = 0.2
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.max_ack_wait = 10
    host_bob.delay = 0.2
    host_bob.add_connection('Alice')
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_bob)

    q_size = 6

    host_alice.run_protocol(qudp_sender, (q_size, host_bob.host_id))
    host_bob.run_protocol(qudp_receiver, (q_size, host_alice.host_id))

    start_time = time.time()
    while time.time() - start_time < 50:
        pass

    network.stop(stop_hosts=True)


if __name__ == '__main__':
    main()
