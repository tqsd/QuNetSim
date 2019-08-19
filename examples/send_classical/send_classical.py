from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve:

        host_alice = Host('00000001', Alice)
        host_alice.add_connection('00000000')
        host_alice.start()

        host_bob = Host('00000000', Bob)
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        print('alice sends message')

        host_alice.send_classical('00000000', 'hello')

        nodes = [host_alice, host_bob, host_eve]

        print(network.get_route(host_alice.host_id, host_eve.host_id))

        start_time = time.time()
        while time.time() - start_time < 3:
            pass

        print('stopping hosts')
        for h in nodes:
            print(h.host_id + 'stopped')
            h.stop()


main()
