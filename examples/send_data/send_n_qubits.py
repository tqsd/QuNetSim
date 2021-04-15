from qunetsim.components import Host, Network
from qunetsim.objects import Logger, Qubit
from qunetsim.backends import SimpleStabilizerBackend
from qunetsim.backends import EQSNBackend
import numpy as np

import time

Logger.DISABLED = True

sender_ids = []
receiver_ids = []


def sender_superdense(host, r, n):
    global sender_ids
    sender_ids = []
    pairs = []
    for i in range(n // 2):
        q1 = Qubit(host)
        q2 = Qubit(host)
        q1.H()
        q1.cnot(q2)
        pairs.append(q1)
        host.send_qubit(r, q2, await_ack=False, no_ack=True)

    bits = np.random.choice([0, 1], size=n)
    print(f'S: {"".join([str(i) for i in list(bits)])}')
    i = 0
    j = 0
    while i < n // 2:
        q = pairs[i]
        b1, b2 = bits[j], bits[j + 1]
        if b2 == 1:
            q.X()
        if b1 == 1:
            q.Z()
        host.send_qubit(r, q, await_ack=False, no_ack=True)
        i += 1
        j += 2


def receiver_superdense(host, s, n):
    global receiver_ids
    pairs = []
    received = []
    while len(pairs) != n // 2:
        q = host.get_data_qubit(s, wait=-1)
        pairs.append(q)

    i = 0
    while i < n // 2:
        q1 = host.get_data_qubit(s, wait=-1)
        q2 = pairs[i]
        q1.cnot(q2)
        q1.H()
        received.append(q1.measure())
        received.append(q2.measure())
        i += 1

    print(f'R: {"".join([str(i) for i in received])}')


def sender(host, r, n):
    global sender_ids
    sender_ids = []
    bits = np.random.choice([0, 1], size=n)
    print(f'S: {"".join([str(i) for i in list(bits)])}')
    for b in bits:
        q = Qubit(host)
        if b == 1:
            q.X()
        sender_ids.append(q.id)
        host.send_qubit(r, q, await_ack=False, no_ack=True)


def receiver(host, s, n):
    global receiver_ids
    receiver_ids = []
    i = 0
    received = []
    while i < n:
        qubits = host.get_data_qubits(s, n=n, wait=-1)
        for q in qubits:
            receiver_ids.append(q.id)
            received.append(q.measure())
        i += int(n / 1)
    print(f'R: {"".join([str(i) for i in received])}')


def receiver_series(host, s, n):
    global receiver_ids
    receiver_ids = []
    received = []
    while len(receiver_ids) != n:
        q = host.get_data_qubit(s, wait=-1)
        receiver_ids.append(q.id)
        received.append(q.measure())
    print(f'R: {"".join([str(i) for i in received])}')


def main():
    network = Network.get_instance()
    back = SimpleStabilizerBackend()
    # back = EQSNBackend()
    network.start(backend=back)
    network.delay = 0.0

    host_alice = Host('Alice', back)
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob', back)
    host_bob.add_connection('Alice')
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_bob)

    n = 400

    start = time.time()

    host_alice.run_protocol(sender_superdense, ('Bob', n))
    # host_bob.run_protocol(receiver_series, ('Alice', n), blocking=True)
    host_bob.run_protocol(receiver_superdense, ('Alice', n), blocking=True)

    end = time.time()
    print(end - start)

    # for i in range(n):
    #     if sender_ids[i] != receiver_ids[i]:
    #         print('FAILED')
    #         break
    # print("WORKED")

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
