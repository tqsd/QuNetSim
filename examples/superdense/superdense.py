from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    network.delay = 0.2
    backend = CQCBackend()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.packet_drop_rate = 0
    network.start(nodes, backend)


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

    time.sleep(2)

    host_alice.send_superdense('Bob', '01', True)

    start_time = time.time()
    while time.time() - start_time < 60:
        pass

    network.stop(True)


if __name__ == '__main__':
    main()
