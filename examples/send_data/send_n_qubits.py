from qunetsim.components import Host, Network
from qunetsim.objects import Logger, Qubit
from qunetsim.backends import SimpleStabilizerBackend

import time

Logger.DISABLED = True

sender_ids = []
receiver_ids = []


def sender(host, r, n):
    global sender_ids
    sender_ids = []
    for _ in range(n):
        q = Qubit(host)
        sender_ids.append(q.id)
        host.send_qubit(r, q, await_ack=False, no_ack=True)


def receiver(host, s, n):
    global receiver_ids
    receiver_ids = []
    i = 0
    while i < n:
        qubits = host.get_data_qubits(s, n=int(n / 1), wait=-1)
        for q in qubits:
            receiver_ids.append(q.id)
            q.measure()
        i += int(n / 1)


def receiver_series(host, s, n):
    global receiver_ids
    receiver_ids = []

    while len(receiver_ids) != n:
        q = host.get_data_qubit(s, wait=-1)
        receiver_ids.append(q.id)
        q.measure()


def main():
    network = Network.get_instance()
    back = SimpleStabilizerBackend()
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

    n = 200

    start = time.time()

    host_alice.run_protocol(sender, ('Bob', n))
    # host_bob.run_protocol(receiver_series, ('Alice', n), blocking=True)
    host_bob.run_protocol(receiver, ('Alice', n), blocking=True)

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
