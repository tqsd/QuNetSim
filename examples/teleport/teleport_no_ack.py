from qunetsim.components.host import Host
from qunetsim.qunetsim.components import Network
from qunetsim.objects import Qubit


def main():
    network = Network.get_instance()
    nodes = ['Alice', 'Bob', 'Eve']
    network.delay = 0.2
    network.start(nodes)

    host_alice = Host('Alice')
    host_bob = Host('Bob')
    host_eve = Host('Eve')

    host_alice.add_connection('Bob')
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_eve.add_connection('Bob')

    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    q = Qubit(host_alice)
    print(q.id)
    q.X()

    host_alice.send_epr('Eve', await_ack=True)
    print('done')
    host_alice.send_teleport('Eve', q, no_ack=True)
    q_eve = host_eve.get_data_qubit(host_alice.host_id, q.id, wait=5)

    assert q_eve is not None
    print(q.id)
    print('Eve measures: %d' % q_eve.measure())
    network.stop(True)


if __name__ == '__main__':
    main()
