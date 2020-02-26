from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit
import components.protocols as protocols


def main():
    backend = CQCBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)

    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    network.delay = 0.1
    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].storage_epr_limit = 1
    hosts['bob'].storage_epr_limit = 1

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    hosts['alice'].max_ack_wait = 10

    hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)
    hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)

    assert hosts['alice'].shares_epr(hosts['bob'].host_id)
    assert len(hosts['alice'].get_epr_pairs(hosts['bob'].host_id)) == 1
    assert hosts['bob'].shares_epr(hosts['alice'].host_id)
    assert len(hosts['bob'].get_epr_pairs(hosts['alice'].host_id)) == 1

    hosts['alice'].set_epr_memory_limit(2, hosts['bob'].host_id)
    hosts['bob'].set_epr_memory_limit(2)

    hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)
    hosts['alice'].send_epr(hosts['bob'].host_id, await_ack=True)

    alice_pairs = hosts['alice'].get_epr_pairs(hosts['bob'].host_id)
    bob_pairs = hosts['bob'].get_epr_pairs(hosts['alice'].host_id)
    assert len(alice_pairs) == 2
    assert len(bob_pairs) == 2

    for q in alice_pairs:
        q.measure()
    for q in bob_pairs:
        q.measure()

    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
