import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
import components.protocols as protocols
from objects.qubit import Qubit


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    backend = CQCBackend()
    network.start(nodes, backend)
    network.delay = 0.7

    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    network.delay = 0
    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    q1 = Qubit(hosts['alice'])
    hosts['alice'].send_qubit('Bob', q1, await_ack=True)
    q1 = Qubit(hosts['alice'])
    hosts['alice'].send_qubit('Bob', q1, await_ack=True)
    q1 = Qubit(hosts['alice'])
    hosts['alice'].send_qubit('Bob', q1, await_ack=True)
    q1 = Qubit(hosts['bob'])
    hosts['bob'].send_qubit('Alice', q1, await_ack=True)
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
