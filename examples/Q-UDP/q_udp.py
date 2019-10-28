from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger
from components.daemon_thread import DaemonThread
from components import protocols


def qudp_sender(host, q_size, receiver_id):

    bit_arr = np.random.randint(2, size=q_size)
    print(bit_arr)
    data_qubits = []

    checksum_size = 1
    checksum_per_qubit = int(q_size / checksum_size)

    for i in range(q_size):
        q_tmp = qubit(host.cqc)
        if bit_arr[i] == 1:
            q_tmp.X()
        data_qubits.append(q_tmp)

    checksum_qubits = protocols._add_checksum(host.cqc , data_qubits , checksum_per_qubit)
    data_qubits.extend(checksum_qubits)
    data_qubits_w_checksum = data_qubits
    print('data_qubits_w_checksum')
    print(data_qubits_w_checksum)
    size_info = []
    size_info.append(checksum_size)
    size_info= str(size_info)
    host.send_classical(receiver_id, size_info, False)

    epr_array = []
    for i in range(len(data_qubits_w_checksum)):
        id = host.send_epr(receiver_id, await_ack= True)
        #epr_array.append(host.get_epr(receiver_id , id ))

    print('epr arrays')
    print(host.get_epr_pairs())

    for i in range(len(data_qubits_w_checksum)):
        print('i')
        print(i)
        host.send_teleport(receiver_id, data_qubits_w_checksum[i])

    print('out of loop')



def qudp_receiver(host, q_size, sender_id):
    wait_time = 10
    messages = host.get_classical(sender_id, wait=wait_time)
    while len(messages)<1:
        messages = host.get_classical(sender_id, wait=wait_time)

    size_info = host.get_classical(sender_id, wait=wait_time)[0]['message']
    size_info = np.fromstring(size_info[1:-1], dtype=int , sep=', ')
    print('size info')
    print(size_info)
    checksum_size = size_info[0]


    wait = 25
    wait_start_time = time.time()
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

    return



def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.1
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:

        host_alice = Host('alice', Alice)
        host_alice.add_connection('bob')
        host_alice.add_c_connection('eve')
        host_alice.max_ack_wait = 10
        host_alice.start()

        host_bob = Host('bob', Bob)
        host_bob.max_ack_wait = 10
        host_bob.add_connection('alice')
        host_bob.add_q_connection('dean')
        host_bob.start()

        host_eve = Host('eve', Eve)
        host_eve.add_c_connection('alice')
        host_eve.add_c_connection('dean')
        host_eve.start()

        host_dean = Host('dean', Dean)
        host_dean.add_q_connection('bob')
        host_dean.add_c_connection('eve')
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        q_size = 5

        DaemonThread(qudp_sender, args=(host_alice, q_size, host_bob.host_id))
        DaemonThread(qudp_receiver, args=(host_bob, q_size, host_alice.host_id))

        nodes = [host_alice, host_bob, host_eve, host_dean]
        start_time = time.time()
        while time.time() - start_time < 100:
            pass

        for h in nodes:
            h.stop()
        network.stop()


if __name__ == '__main__':
    main()
