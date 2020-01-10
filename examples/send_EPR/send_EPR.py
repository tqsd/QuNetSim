import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    backend = CQCBackend()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.1

    # print('')

    host_alice = Host('Alice', backend)
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob', backend)
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve', backend)
    host_eve.add_connection('Bob')
    # host_eve.add_connection('Dean')
    host_eve.start()

    # host_dean = Host('Dean', backend)
    # host_dean.add_connection('Eve')
    # host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    # network.add_host(host_dean)

    print('--- DID THIS ---')
    q_id1 = host_alice.send_epr('Eve', await_ack=True)[0]
    print('--- ENDED THIS ---', q_id1)

    print('Alice', host_alice._EPR_store)
    print('Bob', host_bob._EPR_store)
    print('Eve', host_eve._EPR_store)

    q1 = host_alice.get_epr('Eve', q_id1)
    q2 = host_eve.get_epr('Alice', q_id1)

    print(host_eve.get_epr_pairs('Alice'))

    if q1 is not None and q2 is not None:
        m1 = q1.measure()
        m2 = q2.measure()

        print("Results of the measurements for q_id_1 are ")
        print(m1)
        print(m2)
    else:
        if q1 is None:
            print('q1 is none')
        if q2 is None:
            print('q2 is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
