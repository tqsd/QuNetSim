from qunetsim.components.host import Host
from qunetsim.qunetsim.components import Network


def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.2

    host_alice = Host('Alice', backend)
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob', backend)
    host_bob.add_connections(['Alice', 'Eve'])
    host_bob.start()

    host_eve = Host('Eve', backend)
    host_eve.add_connections(['Bob', 'Dean'])
    host_eve.start()

    host_dean = Host('Dean', backend)
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_hosts([host_alice, host_bob, host_eve, host_dean])

    print('alice sends message')
    host_alice.send_classical('Bob', 'hello1')
    host_alice.send_classical('Bob', 'hello2')
    host_alice.send_classical('Bob', 'hello3')
    host_alice.send_classical('Bob', 'hello4')
    host_alice.send_classical('Bob', 'hello5')
    host_alice.send_classical('Bob', 'hello6')
    host_alice.send_classical('Bob', 'hello7')
    host_alice.send_classical('Bob', 'hello8')
    host_alice.send_classical('Bob', 'hello9')
    host_alice.send_classical('Bob', 'hello10')

    start_time = time.time()
    while time.time() - start_time < 10:
        pass

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
