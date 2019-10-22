from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger


def qkd_sender(host, q_size, receiver_id):
    bit_arr = np.random.randint(2, size=q_size)
    base_arr = np.random.randint(2, size=q_size)  # 0 represents X basis , 1 represents Z basis
    wait_time = 10
    q_arr = []
    for i in range(q_size):
        q_arr.append(qubit(host.cqc))
        if bit_arr[i] == 1:
            q_arr[i].X()
        if base_arr[i] == 1:
            q_arr[i].H()

    for i in range(q_size):
        host.send_qubit(receiver_id, q_arr[i], await_ack=True)

    messages = host.get_classical(receiver_id, wait=wait_time)
    while len(messages) < q_size + 1:
        messages = host.get_classical(receiver_id, wait=wait_time)

    intended_message = messages[-1]['message']
    message_edited = np.fromstring(intended_message[1:-1], dtype=np.int, sep=' ')
    check = []

    for i in range(q_size):
        # 1 means they have chosen the correct base and 0 otherwise.
        if base_arr[i] == message_edited[i]:
            check.append(i)

    check = np.asarray(check)

    host.send_classical(receiver_id, str(check), True)
    message = host.get_classical(receiver_id, wait=wait_time)
    while len(message) < q_size + 3:
        message = host.get_classical(receiver_id, wait=wait_time)

    intended_message_2 = message[-1]['message']
    message_3_edited = np.fromstring(intended_message_2[1:-1], dtype=np.int, sep=' ')
    confirmation = True

    for i in range(q_size):
        if message_3_edited[i] == 0 or message_3_edited[i] == 1:
            if message_3_edited[i] != bit_arr[i]:
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
    wait_time = 10

    for i in range(q_size):
        q = host.get_data_qubit(sender_id, wait=wait_time)
        if base_arr[i] == 1:
            q['q'].H()
        bit_arr.append(q['q'].measure())

    bit_arr = np.asarray(bit_arr[::-1])
    host.send_classical(sender_id, str(base_arr), True)

    messages = host.get_classical(sender_id, wait=wait_time)
    while len(messages) < 2:
        messages = host.get_classical(sender_id, wait=wait_time)

    message_2 = host.get_classical(sender_id, wait=wait_time)[1]['message']
    message_2_edited = np.fromstring(message_2[1:-1], dtype=np.int, sep=' ')

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

    message_4 = messages[-1]['message']
    shared_key = []

    if message_4 == 'True':
        for i in range(len(message_2_edited)):
            shared_key.append(bit_arr[(message_2_edited[i])])

    Logger.get_instance().log("Receiver's key: " + str(shared_key))


def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.5
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:

        host_alice = Host('alice', Alice)
        host_alice.add_connection('bob')
        host_alice.start()

        host_bob = Host('bob', Bob)
        host_bob.add_connection('alice')
        # host_bob.add_connection('eve')
        host_bob.start()

        # host_eve = Host('eve', Eve)
        # host_eve.add_connection('bob')
        # host_eve.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        # network.add_host(host_eve)

        q_size = 5

        qkd_sender(host_alice, q_size, host_bob.host_id)
        qkd_receiver(host_bob, q_size, host_alice.host_id)

        nodes = [host_alice, host_bob]

        start_time = time.time()
        while time.time() - start_time < 20:
            pass

        for h in nodes:
            h.stop()
        network.stop()


if __name__ == '__main__':
    main()
