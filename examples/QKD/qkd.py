from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger
from components.daemon_thread import DaemonThread


def qkd_sender(host, q_size, receiver_id):
    bit_arr = np.random.randint(2, size=q_size)
    base_arr = np.random.randint(2, size=q_size)  # 0 represents X basis , 1 represents Z basis
    wait_time = 8

    q_arr = []
    for i in range(q_size):
        q_arr.append(qubit(host.cqc))
        if bit_arr[i] == 1:
            q_arr[i].X()
        if base_arr[i] == 1:
            q_arr[i].H()

    for i in range(q_size):
        host.send_qubit(receiver_id, q_arr[i], await_ack=True)

    messages = []
    while len(messages) < q_size + 1:
        messages = host.get_classical(receiver_id, wait=wait_time)

    intended_message = ''
    for m in messages:
        if m['sequence_number'] == q_size and m['message'] != 'ACK':
            intended_message = m['message']
            break

    if intended_message == '':
        print('sender failed')
        return

    message_edited = np.fromstring(intended_message[1:-1], dtype=np.int, sep=' ')
    check = []

    for i in range(q_size):
        # 1 means they have chosen the correct base and 0 otherwise.
        if base_arr[i] == message_edited[i]:
            check.append(i)

    check = np.asarray(check)

    host.send_classical(receiver_id, str(check), True)
    messages = host.get_classical(receiver_id, wait=wait_time)
    while len(messages) < q_size + 3:
        messages = host.get_classical(receiver_id, wait=wait_time)
    intended_message = ''
    for m in messages:
        if m['sequence_number'] == q_size + 2 and m['message'] != 'ACK' :
            intended_message = m['message']
            break

    if intended_message == '':
        print('sender failed')
        return

    message_edited = np.fromstring(intended_message[1:-1], dtype=np.int, sep=' ')
    confirmation = True
    for i in range(q_size):
        if message_edited[i] == 0 or message_edited[i] == 1:
            if message_edited[i] != bit_arr[i]:
                confirmation = False

    shared_key = []
    if confirmation:
        for i in range(len(check)):
            shared_key.append(bit_arr[(check[i])])

    Logger.get_instance().log("Sender's key: " + str(shared_key))
    host.send_classical(receiver_id, str(confirmation))


def qkd_receiver(host, q_size, sender_id):
    bit_arr = []
    base_arr = np.random.randint(2, size=q_size)
    wait_time = 8

    for i in range(q_size):
        q = host.get_data_qubit(sender_id, wait=wait_time)
        if base_arr[i] == 1:
            q['q'].H()
        bit_arr.append(q['q'].measure())

    bit_arr = np.asarray(bit_arr[::-1])
    while host.get_sequence_number(sender_id) != q_size:
        pass
    host.send_classical(sender_id, str(base_arr), True)

    messages = host.get_classical(sender_id, wait=wait_time)
    while len(messages) < 2:
        messages = host.get_classical(sender_id, wait=wait_time)

    message_2 = host.get_classical(sender_id, wait=wait_time)
    for m in message_2:
        if m['message'] != 'ACK':
            message_2_edited = m['message']
            break
    message_2_edited = np.fromstring(message_2_edited[1:-1], dtype=np.int, sep=' ')

    reveal_arr_pos = np.random.randint(2, size=len(message_2_edited))
    reveal_bit = []
    bit_arr = bit_arr[::-1]
    count = 0
    for i in range(q_size):
        if count < len(message_2_edited) and i == message_2_edited[count]:
            if reveal_arr_pos[count] == 1:
                reveal_bit.append(bit_arr[i])
                count = count + 1
            else:
                reveal_bit.append(2)
                count = count + 1
        else:
            reveal_bit.append(2)

    reveal_bit = np.asarray(reveal_bit)
    host.send_classical(sender_id, str(reveal_bit), True)

    messages = host.get_classical(sender_id, wait=wait_time)
    while len(messages) < 4:
        messages = host.get_classical(sender_id, wait=wait_time)

    message = messages[0]['message']
    if message == '':
        print('receiver failed')
        return

    shared_key = []
    if message == 'True':
        for i in range(len(message_2_edited)):
            shared_key.append(bit_arr[(message_2_edited[i])])

    Logger.get_instance().log("Receiver's key: " + str(shared_key))


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    print('')

    with CQCConnection("Alice") as A, CQCConnection("Bob") as node_1, \
            CQCConnection('Eve') as node_2, CQCConnection('Dean') as B:

        A = Host('A', A)
        A.add_q_connection('node_1')
        A.add_c_connection('node_2')
        A.start()

        node_1 = Host('node_1', node_1)
        node_1.add_q_connection('B')
        node_1.start()

        node_2 = Host('node_2', node_2)
        node_2.add_c_connection('A')
        node_2.add_c_connection('B')
        node_2.start()

        B = Host('B', B)
        B.add_c_connection('node_2')
        B.start()

        network.add_host(A)
        network.add_host(node_1)
        network.add_host(node_2)
        network.add_host(B)

        q_size = 8

        DaemonThread(qkd_sender, args=(A, q_size, B.host_id))
        DaemonThread(qkd_receiver, args=(B, q_size, A.host_id))

        nodes = [A, node_1, node_2, B]
        start_time = time.time()
        while time.time() - start_time < 50:
            pass

        for h in nodes:
            h.stop()
        network.stop()


if __name__ == '__main__':
    main()
