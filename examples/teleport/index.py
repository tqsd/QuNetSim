from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from beyond_cringe import EQSNBackend
from time import perf_counter
import numpy


def main():
    backend = EQSNBackend()

    network = Network.get_instance()
    network.start(backend=backend)

    host_alice = Host('Alice')
    host_bob = Host('Bob')
    host_eve = Host('Eve')

    host_alice.add_connection('Bob')
    host_bob.add_connections(['Alice', 'Eve'])
    host_eve.add_connection('Bob')

    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_hosts([host_alice, host_bob, host_eve])

    q = Qubit(host_alice)
    #print(q.id)
    q.H()

    host_alice.send_epr('Eve', await_ack=True)
    #print('done')
    host_alice.send_teleport('Eve', q, await_ack=True)
    q_eve = host_eve.get_qubit(host_alice.host_id, q.id, wait=0)

    assert q_eve is not None
    #print('Eve measures: %d' % q_eve.measure())
    network.stop(True)


if __name__ == '__main__':
    data = []
    for n in range (30):
        start = perf_counter()
        for i in range(10):
            main()
        end = perf_counter()
        data.append(1000*(end - start))
        print(n + 1, "/30 rounds done.")
    print(data)
    print("avg:", numpy.average(data))
    print("std:", numpy.std(data))
    
