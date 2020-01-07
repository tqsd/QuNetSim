from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    network.delay = 0.2
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.packet_drop_rate = 0
    network.start(nodes, backend)

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob, \
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

        time.sleep(2)

        host_alice.send_superdense('00000001', '01', True)

        start_time = time.time()
        while time.time() - start_time < 60:
            pass

        network.stop(True)


if __name__ == '__main__':
    main()
