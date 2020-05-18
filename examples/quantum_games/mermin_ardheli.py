import time

from components.host import Host
from components.network import Network
import random
import numpy as np

from objects.qubit import Qubit


def referee(host, players):
    host.empty_classical()
    # Distribute a GHZ state to the players
    print('sending ghz')
    host.send_ghz(players, distribute=True, await_ack=True)
    print('acks ghz received')

    # Send each party a random bit
    sent = []
    for p in players:
        sent.append(random.choice([0, 1]))
        host.send_classical(p, sent[-1])

    responses = []
    for p in players:
        responses.append(host.get_classical(p, wait=10)[0].content)

    w = 1 if sum(sent) % 4 in [0, 1] else 0
    a = responses[0]
    for response in responses:
        a ^= response

    if w == a:
        print('winners')
    else:
        print('losers')


def classical_player(host, ref):
    host.empty_classical()
    q = host.get_ghz(ref, wait=10)
    print('%s got ghz' % host.host_id)
    x = host.get_classical(ref, wait=10)[0].content
    print('%s received message from ref: %d' % (host.host_id, x))
    host.send_classical(ref, 0)


def quantum_player(host, ref):
    host.empty_classical()
    q = host.get_ghz(ref, wait=10)
    print('%s got ghz' % host.host_id)
    x = host.get_classical(ref, wait=10)[0].content

    if x == 0:
        q.custom_gate(np.array([[1, 0], [0, 1]]))
    else:
        q.custom_gate((1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))

    print('%s received message from ref: %d' % (host.host_id, x))
    host.send_classical(ref, q.measure())


def node(host, distributor):
    q = host.get_ghz(distributor, wait=10)
    if q is None:
        print('failed')
        return
    q.H()
    m = q.measure()
    host.send_broadcast(str(m))


def main():
    network = Network.get_instance()
    network.start()

    host_A = Host('Ref')
    host_A.add_connections(['B', 'C', 'D', 'E'])
    host_A.start()
    host_B = Host('B')
    host_B.add_connections(['Ref'])
    host_B.start()
    host_C = Host('C')
    host_C.add_connections(['Ref'])
    host_C.start()
    host_D = Host('D')
    host_D.add_connections(['Ref'])
    host_D.start()
    host_E = Host('E')
    host_E.add_connections(['Ref'])
    host_E.start()

    network.add_hosts([host_A, host_B, host_C, host_D, host_E])

    print('starting')
    for i in range(1):
        host_B.run_protocol(quantum_player, (host_A.host_id,))
        host_C.run_protocol(quantum_player, (host_A.host_id,))
        host_D.run_protocol(quantum_player, (host_A.host_id,))
        host_E.run_protocol(quantum_player, (host_A.host_id,))
        host_A.run_protocol(referee, ([host_B.host_id, host_C.host_id, host_D.host_id, host_E.host_id],), blocking=True)
        time.sleep(0.5)
    network.stop(True)


if __name__ == '__main__':
    main()
