from qunetsim.components import Host
from qunetsim.objects import Logger
from qunetsim.components import Network
from qunetsim.backends import CQCBackend

Logger.DISABLED = False


def main():
    backend = CQCBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.1
    network.use_ent_swap = True

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

    q_id1, _ = host_alice.send_epr('Dean', await_ack=True)

    q1 = host_alice.get_epr('Dean', q_id1)
    q2 = host_dean.get_epr('Alice', q_id1)

    if q1 is not None and q2 is not None:
        m1 = q1.measure()
        m2 = q2.measure()
        print("Results of the measurements for the entangled pair are %d %d" % (m1, m2))
    else:
        if q1 is None:
            print('q1 is none')
        if q2 is None:
            print('q2 is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
