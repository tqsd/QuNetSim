from qunetsim.components import Host
from qunetsim.objects import Logger, Qubit
from qunetsim.components.emulated_network import EmulatedNetwork
from qunetsim.backends.emulated_backend import EmulationBackend
import time

Logger.DISABLED = False


def main():
    backend = EmulationBackend()
    network = EmulatedNetwork.get_instance()
    nodes = ["Alice"]
    network.start(nodes)

    host_alice = Host('Alice', backend)
    host_alice.start()

    network.add_host(host_alice)

    # q = Qubit(host_alice)
    q = Qubit(host_alice)
    q.X()
    # q.X()
    # q.X()
    # q.X()
    # q.X()

    m = q.measure()

    print(m)

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
