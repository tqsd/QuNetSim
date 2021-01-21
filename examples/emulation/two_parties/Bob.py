from qunetsim.components import Host
from qunetsim.objects import Logger
from qunetsim.components.emulated_network import EmulatedNetwork
from qunetsim.backends.emulated_backend import EmulationBackend

Logger.DISABLED = False


def main():
    backend = EmulationBackend()
    network = EmulatedNetwork.get_instance()
    nodes = ["Bob"]
    network.start(nodes, backend)

    host_bob = Host('Bob', backend)
    host_bob.add_connection('Alice')
    host_bob.start()

    network.add_host(host_bob)

    q1 = host_bob.get_epr('Alice', wait=10)

    if q1 is not None:
        m1 = q1.measure()
        print("Results for Bob is %d" % (m1))
    else:
        print('q1 is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
