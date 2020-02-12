from components.host import Host
from components.network import Network
import time


def main():
    network = Network.get_instance()
    network.delay = 0.1
    nodes = ["Alice", "Bob", "Eve"]
    network.start(nodes)

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    host_alice.send_superdense('Eve', '11')
    host_alice.send_superdense('Eve', '10')
    host_alice.send_superdense('Eve', '00')

    time.sleep(5)
    messages = host_eve.get_classical('Alice')

    for m in messages:
        print('----')
        print(m)
        print('----')


if __name__ == '__main__':
    main()
