from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit


def main():
    network = Network.get_instance()
    network.start()

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
    print(q.id)
    q.X()

    host_alice.send_epr('Eve', await_ack=True)
    print('done')
    host_alice.send_teleport('Eve', q, await_ack=True)
    q_eve = host_eve.get_qubit(host_alice.host_id, q.id, wait=5)

    assert q_eve is not None
    print(q.id)
    print('Eve measures: %d' % q_eve.measure())
    network.stop(True)


if __name__ == '__main__':
    main()
