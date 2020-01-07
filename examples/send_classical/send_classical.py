from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from components.host import Host
from backends.cqc_backend import CQCBackend
from components.network import Network


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.2
    network.packet_drop_rate = 0
    print('')

    backend = CQCBackend()


    host_alice = Host('Alice', backend)
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob', backend)
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve', backend)
    host_eve.add_connection('Bob')
    host_eve.add_connection('Dean')
    host_eve.start()

    host_dean = Host('Dean', backend)
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)


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

    time.sleep(10)
    bob_messages = host_bob.classical
    print(len(bob_messages))

    start_time = time.time()
    while time.time() - start_time < 10:
        pass

    network.stop(True)
    exit()

if __name__ == '__main__':
    main()
