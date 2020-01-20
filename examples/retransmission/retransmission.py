import random
from components.host import Host
from components.network import Network
from cqc.pythonLib import CQCConnection, qubit
import time

WAIT_TIME = 15
MAX_TRIAL_NUM = 10


def retransmission_sender(host, receiver_id, trial_num):
    q = qubit(host.cqc)
    q.H()

    q_received = False
    trials = 0
    while (not q_received) and trials < trial_num:
        print('Alice prepares qubit')

        err_1 = qubit(host.cqc)

        # encode logical qubit
        q.cnot(err_1)

        host.send_qubit(receiver_id, q, await_ack=False)
        m = host.get_classical(receiver_id, wait=WAIT_TIME)[0].content
        # if ACK
        if m == '1':
            print('Alice: Bob received the qubit')
            # Remove err_1 from simulqron
            err_1.measure()
            q_received = True
        else:
            print('Alice: Bob did not receive the qubit')
            # re-introduce a qubit to the system and correct the error
            q = qubit(host.cqc)
            err_1.cnot(q)
        trials += 1
    if trials == 10:
        print("Alice: too many attempts made")


def retransmission_receiver(host, sender_id, trial_num):
    success_prob = 0.5
    q_received = False
    trial = 0
    while (not q_received) and trial < trial_num:
        q = host.get_data_qubit(sender_id, wait=WAIT_TIME)['q']
        if random.random() <= success_prob:
            q_received = True
            m = q.measure()
            print('Bob: received qubit: ', m)
            host.send_classical(sender_id, '1')
        else:
            print("Bob: didn't receive the qubit")
            host.send_classical(sender_id, '0')
            # Simulate qubit loss
            q.release()
        trial += 1

    if trial == trial_num:
        print("Bob: too many attempts made")


def main():
    global thread_1_return
    global thread_2_return

    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.5

    host_alice = Host('alice')
    host_alice.add_connection('bob')
    host_alice.max_ack_wait = 30
    host_alice.delay = 0.2
    host_alice.start()

    host_bob = Host('bob')
    host_bob.max_ack_wait = 30
    host_bob.delay = 0.2
    host_bob.add_connection('alice')
    host_bob.add_connection('eve')
    host_bob.start()

    host_eve = Host('eve')
    host_eve.max_ack_wait = 30
    host_eve.delay = 0.2
    host_eve.add_connection('bob')
    host_eve.add_connection('dean')
    host_eve.start()

    host_dean = Host('dean')
    host_dean.max_ack_wait = 30
    host_dean.delay = 0.2
    host_dean.add_connection('eve')
    host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)

    host_alice.run_protocol(retransmission_sender, (host_dean.host_id, MAX_TRIAL_NUM))
    host_dean.run_protocol(retransmission_receiver, (host_alice.host_id, MAX_TRIAL_NUM))

    start_time = time.time()
    while time.time() - start_time < 150:
        pass

    network.stop(stop_hosts=True)
    exit()


if __name__ == '__main__':
    main()
