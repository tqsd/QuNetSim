from qunetsim.components import Host
from qunetsim.objects import Logger
from qunetsim.components.emulated_network import EmulatedNetwork
from qunetsim.backends.emulated_backend import EmulationBackend

Logger.DISABLED = False


def main():
    backend = EmulationBackend()
    network = EmulatedNetwork.get_instance()
    nodes = ["Alice"]
    network.start(nodes, backend)

    host_alice = Host('Alice', backend)
    host_alice.add_connection('Bob')
    host_alice.start()

    network.add_host(host_alice)

    q_id1, _ = host_alice.send_epr('Bob', await_ack=True)

    q1 = host_alice.get_epr('Bob', q_id1)

    if q1 is not None:
        m1 = q1.measure()
        print("Results for Alice is %d" % (m1))
    else:
        print('q1 is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
