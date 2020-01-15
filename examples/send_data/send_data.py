import sys

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit


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
    q = Qubit(host_alice)
    q.X()
    q_id, _ = host_alice.send_qubit('Eve', q, await_ack=True)
    print('--- ENDED THIS ---', q_id)

    # print('Alice\n', host_alice._data_qubit_store)
    print('Bob\n', host_bob._data_qubit_store)
    print('Eve\n', host_eve._data_qubit_store)

    q_rec = host_eve.get_data_qubit('Alice', q_id)

    if q_rec is not None:
        m = q_rec.measure()
        print("Results of the measurements for q_id are ", str(m))
    else:
        print('q_rec is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
