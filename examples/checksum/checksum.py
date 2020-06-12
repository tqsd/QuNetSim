import time
import numpy as np

from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Logger
from qunetsim.objects import Qubit

WAIT_TIME = 10




def checksum_sender(host, q_size, receiver_id, checksum_size_per_qubit):
    bit_arr = np.random.randint(2, size=q_size)
    Logger.get_instance().log('Bit array to be sent: ' + str(bit_arr))
    qubits = []
    for i in range(q_size):
        q_tmp = Qubit(host)
        if bit_arr[i] == 1:
            q_tmp.X()
        qubits.append(q_tmp)

    check_qubits = host.add_checksum(qubits, checksum_size_per_qubit)
    checksum_size = int(q_size / checksum_size_per_qubit)
    qubits.append(check_qubits)
    checksum_cnt = 0
    for i in range(q_size + checksum_size):
        if i < q_size:
            q = qubits[i]
        else:
            q = qubits[q_size][checksum_cnt]
            checksum_cnt = checksum_cnt + 1

        host.send_qubit(receiver_id, q, await_ack=True)


def checksum_receiver(host, q_size, sender_id, checksum_size_per_qubit):
    qubits = []
    checksum_size = int(q_size / checksum_size_per_qubit)
    while len(qubits) < (q_size + checksum_size):
        q = host.get_data_qubit(sender_id, wait=WAIT_TIME)
        qubits.append(q)
        Logger.get_instance().log(str(host.host_id) + ': received qubit')

    checksum_qubits = []
    checksum_cnt = 0

    for i in range(len(qubits)):
        if checksum_cnt < checksum_size:
            checksum_qubits.append(qubits[q_size + i]['q'])
            checksum_cnt = checksum_cnt + 1

    checksum_cnt = 1
    for i in range(len(qubits) - checksum_size):
        qubits[i]['q'].cnot(checksum_qubits[checksum_cnt - 1])
        if i == (checksum_cnt * checksum_size_per_qubit - 1):
            checksum_cnt = checksum_cnt + 1

    errors = 0
    for i in range(len(checksum_qubits)):
        if checksum_qubits[i].measure() != 0:
            errors += 1

    print('---------')
    if errors == 0:
        Logger.get_instance().log('No error exist in UDP packet')
    else:
        Logger.get_instance().log('There were errors in the UDP transmission')
    print('---------')

    rec_bits = []
    for i in range(len(qubits) - checksum_size):
        rec_bits.append(qubits[i]['q'].measure())

    if errors == 0:
        print('---------')
        Logger.get_instance().log('Receiver received the classical bits: ' + str(rec_bits))
        print('---------')
        return True

    return


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.5

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.max_ack_wait = 30
    host_alice.delay = 0.2
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.max_ack_wait = 30
    host_bob.delay = 0.2
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.max_ack_wait = 30
    host_eve.delay = 0.2
    host_eve.add_connection('Bob')
    host_eve.add_connection('Dean')
    host_eve.start()

    host_dean = Host('Dean')
    host_dean.max_ack_wait = 30
    host_dean.delay = 0.2
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)

    network.x_error_rate = 0
    network.packet_drop_rate = 0

    q_size = 6
    checksum_per_qubit = 2

    host_alice.run_protocol(checksum_sender, (q_size, host_dean.host_id, checksum_per_qubit))
    host_dean.run_protocol(checksum_receiver, (q_size, host_alice.host_id, checksum_per_qubit))

    start_time = time.time()
    while time.time() - start_time < 150:
        pass

    network.stop(stop_hosts=True)
    exit()


if __name__ == '__main__':
    main()
