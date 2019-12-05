from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.2
    network.packet_drop_rate = 0
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:

        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000000')
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)
        host_eve.add_connection('00000001')
        host_eve.add_connection('00000111')
        host_eve.start()

        host_dean = Host('00000111', Dean)
        host_dean.add_connection('00000011')
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)


        print('alice sends message')

        host_alice.send_classical('00000001', 'hello1')
        host_alice.send_classical('00000001', 'hello2')
        host_alice.send_classical('00000001', 'hello3')
        host_alice.send_classical('00000001', 'hello4')
        host_alice.send_classical('00000001', 'hello5')
        host_alice.send_classical('00000001', 'hello6')
        host_alice.send_classical('00000001', 'hello7')
        host_alice.send_classical('00000001', 'hello8')
        host_alice.send_classical('00000001', 'hello9')
        host_alice.send_classical('00000001', 'hello10')

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
