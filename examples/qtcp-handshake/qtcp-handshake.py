import time
import sys

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger
from cqc.pythonLib import CQCConnection, qubit

thread_1_return = None
thread_2_return = None

SYN = '10'
SYN_ACK = '11'
ACK = '01'
WAIT_TIME = 15
MAX_NUM_OF_TRANSMISSIONS = 10


def handshake_sender(host, receiver_id):
    """
    Establishes a classical TCP-like handshake with the receiver .
    If successful starts the transmission of qubits , otherwise terminated the connection.

    :param host: Sender of qubits
    :param receiver_id: ID of the receiver
    :return: If successful returns True, otherwise False
    """

    # Create an EPR pair.
    qa_1 = qubit(host.cqc)
    qa_2 = qubit(host.cqc)

    qa_1.H()
    qa_1.cnot(qa_2)

    # Send a half of EPR pair and the SYN message to Bob.
    _, ack_received = host.send_qubit(receiver_id, qa_2, await_ack=True)
    if ack_received is False:
        Logger.get_instance().log('ACK is not received')
        return False
    ack_received = host.send_classical(receiver_id, SYN, await_ack=True)
    if ack_received is False:
        Logger.get_instance().log('ACK is not received')
        return False

    syn_seq_num = host.get_sequence_number(receiver_id)

    # Receive the qubits Bob has sent (qubit 2 and qubit 3) for SYN-ACK.
    qb_2 = host.get_data_qubit(receiver_id, wait=WAIT_TIME)
    if qb_2 is None:
        return False
    qb_2 = qb_2['q']

    qb_3 = host.get_data_qubit(receiver_id, wait=WAIT_TIME)
    if qb_3 is None:
        return False
    qb_3 = qb_3['q']

    # Receive the classical message Bob has sent for SYN-ACK.
    message_recv = host.get_message_w_seq_num(receiver_id, syn_seq_num + 2, wait=WAIT_TIME)
    if message_recv is None:
        return False
    message_recv = message_recv[0]['message']
    if message_recv == '11':
        Logger.get_instance().log("SYN-ACK is received by Alice")
    else:
        Logger.get_instance().log('Connection terminated - 1 ')
        return False

    # Make a Bell State measurement on qubit 1 and qubit 2.
    qa_1.cnot(qb_2)
    qa_1.H()
    qa_1_check = qa_1.measure()
    qb_2_check = qb_2.measure()

    # If measurement results are as expected, send Bob a ACK message and the qubit 3 that he has sent previously.
    # Else report that there is something wrong.
    if qa_1_check == 0 and qb_2_check == 0:
        latest_seq_num = host.get_sequence_number(receiver_id)
        ack_received = host.send_classical(receiver_id, ACK, True)
        if ack_received is False:
            Logger.get_instance().log('ACK is not received')
            return False
        _, ack_received = host.send_qubit(receiver_id, qb_3, True)
        if ack_received is False:
            Logger.get_instance().log('ACK is not received')
            return False
        start_time = time.time()
        while time.time() - start_time < WAIT_TIME:
            if host.get_sequence_number(receiver_id) == latest_seq_num + 2 and host.classical[0]['message'] == 'ACK':
                return True
        return False
    else:
        Logger.get_instance().log("Something is wrong.")
        return False


def handshake_receiver(host, sender_id):
    """
    Establishes a classical TCP-like handshake with the sender .
    If successful starts to receive the qubits , otherwise terminated the connection.

    :param host: Receiver host
    :param sender_id: ID of the sender
    :return: If successful returns True, otherwise False
    """
    latest_seq_num = host.get_sequence_number(sender_id)

    # Receive the EPR half of Alice and the SYN message
    qb_2 = host.get_data_qubit(sender_id, wait=WAIT_TIME)
    if qb_2 is None:
        Logger.get_instance().log('qb_2 is None')
        return False
    qb_2 = qb_2['q']

    message_recv = host.get_message_w_seq_num(sender_id, (latest_seq_num + 1), wait=WAIT_TIME)
    if not message_recv:
        Logger.get_instance().log('No message has arrived')
        return False

    message_recv = message_recv[0]['message']

    if message_recv == '10':
        Logger.get_instance().log("SYN is received by Bob")
    else:
        return False

    # Create an EPR pair.
    qb_3 = qubit(host.cqc)
    qb_4 = qubit(host.cqc)
    qb_3.H()
    qb_3.cnot(qb_4)

    # Send half of the EPR pair created (qubit 3) and send back the qubit 2 that Alice has sent first.
    _, ack_received = host.send_qubit(sender_id, qb_2, await_ack=True)

    if ack_received is False:
        Logger.get_instance().log('ACK is not received')
        return False

    _, ack_received = host.send_qubit(sender_id, qb_3, await_ack=True)
    if ack_received is False:
        Logger.get_instance().log('ACK is not received')
        return False

    # Send SYN-ACK message.
    host.send_classical(sender_id, SYN_ACK, True)
    latest_seq_num = host.get_sequence_number(sender_id)

    # Receive the ACK message.
    start_time = time.time()
    ack_message_received = False
    while time.time() - start_time < WAIT_TIME and not ack_message_received:
        latest_messages = host.get_message_w_seq_num(sender_id, latest_seq_num)
        for messages in latest_messages:
            if messages['message'] == '01':
                Logger.get_instance().log('ACK is received by Bob')
                ack_message_received = True

        if ack_message_received:
            break

    # Receive the qubit 3.
    qa_3 = host.get_data_qubit(sender_id, wait=WAIT_TIME)
    if qa_3 is None:
        return False
    qa_3 = qa_3['q']

    # Make a Bell State measurement in qubit 3 and qubit 4.
    qa_3.cnot(qb_4)
    qa_3.H()

    qa_3_check = qa_3.measure()
    qb_4_check = qb_4.measure()

    # If measurement results are as expected , establish the TCP connection.
    # Else report that there is something wrong.
    if qa_3_check == 0 and qb_4_check == 0:
        Logger.get_instance().log("TCP connection established.")
        return True
    else:
        Logger.get_instance().log("Something is wrong.")
        return False


def main():
    global thread_1_return
    global thread_2_return

    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.5

    print('')
    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, CQCConnection('Eve') as Eve, CQCConnection(
            'Dean') as Dean:
        host_alice = Host('alice', Alice)
        host_alice.add_connection('bob')
        host_alice.max_ack_wait = 30
        host_alice.delay = 0.2
        host_alice.start()

        host_bob = Host('bob', Bob)
        host_bob.max_ack_wait = 30
        host_bob.delay = 0.2
        host_bob.add_connection('alice')
        host_bob.add_connection('eve')
        host_bob.start()

        host_eve = Host('eve', Eve)
        host_eve.max_ack_wait = 30
        host_eve.delay = 0.2
        host_eve.add_connection('bob')
        host_eve.add_connection('dean')
        host_eve.start()

        host_dean = Host('dean', Dean)
        host_dean.max_ack_wait = 30
        host_dean.delay = 0.2
        host_dean.add_connection('eve')
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        network.x_error_rate = 0
        network.packet_drop_rate = 0

        host_alice.run_protocol(handshake_sender, (host_dean.host_id, 3))
        host_dean.run_protocol(handshake_receiver, (host_alice.host_id, 3))

        start_time = time.time()
        while time.time() - start_time < 150:
            pass

        network.stop(stop_hosts=True)
        exit()


if __name__ == '__main__':
    main()
