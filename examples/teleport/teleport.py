from components.host import Host
from components.network import Network
from objects.qubit import Qubit
import time

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
    q.X()

    print('did this 1')
    host_alice.send_teleport('Eve', q, await_ack=True)
    print('did this 2')

    time.sleep(2)
    print('did this 3')
    print(host_eve.data_qubit_store)

    # q_eve = host_eve.get_data_qubit(host_alice.host_id, q.id, wait=5)
    # assert q_eve is not None
    # print('Eve measures: %d' % q_eve.measure())


if __name__ == '__main__':
    main()
