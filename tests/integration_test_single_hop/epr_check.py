from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit


def main():
    backend = CQCBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.7
    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}


    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()


    for h in hosts.values():
        network.add_host(h)

    q_id = hosts['alice'].send_epr(hosts['bob'].host_id)
    q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
    i = 0
    while q1 is None and i < 5:
        q1 = hosts['alice'].get_epr(hosts['bob'].host_id, q_id)
        i += 1
        time.sleep(1)

    assert q1 is not None
    i = 0
    q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
    while q2 is None and i < 5:
        q2 = hosts['bob'].get_epr(hosts['alice'].host_id, q_id)
        i += 1
        time.sleep(1)

    assert q2 is not None
    assert (q1.measure() == q2.measure())
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
