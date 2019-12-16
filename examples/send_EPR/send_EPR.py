from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.7

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

    q_id1 = host_alice.send_epr('Dean')
    time.sleep(15)

    q1 = host_alice.get_epr('Dean', q_id1)
    q2 = host_eve.get_epr('Alice', q_id1)

    if q1 is not None and q2 is not None:
        m1 = q1.measure()
        m2 = q2.measure()

        print("Results of the measurements for q_id1 are ")
        print(m1)
        print(m2)
    else:
        print('failed')

    start_time = time.time()
    while time.time() - start_time < 20:
        pass

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
