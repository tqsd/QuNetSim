import time
from qunetsim.components.host import Host
from qunetsim.qunetsim.components import Network


def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.2

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.add_connections(['Alice', 'Eve'])
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connections(['Bob', 'Dean'])
    host_eve.start()

    host_dean = Host('Dean')
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_hosts([host_alice, host_bob, host_eve, host_dean])

    print('alice sends message')
    host_alice.send_classical('Bob', 'hello1', no_ack=True)
    host_alice.send_classical('Bob', 'hello2', no_ack=True)
    host_alice.send_classical('Bob', 'hello3', no_ack=True)
    host_alice.send_classical('Bob', 'hello4', no_ack=True)
    host_alice.send_classical('Bob', 'hello5', no_ack=True)
    host_alice.send_classical('Bob', 'hello6', no_ack=True)
    host_alice.send_classical('Bob', 'hello7', no_ack=True)
    host_alice.send_classical('Bob', 'hello8', no_ack=True)
    host_alice.send_classical('Bob', 'hello9', no_ack=True)
    host_alice.send_classical('Bob', 'hello10', no_ack=True)

    start_time = time.time()
    while time.time() - start_time < 10:
        pass

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
