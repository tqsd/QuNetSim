import sys
import time

sys.path.append("../..")
from qunetsim.components.host import Host
from qunetsim.components.network import Network

MAX_WAIT = 20

def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    hosts = {'alice': Host('Alice'),
             'bob': Host('Bob'),
             'eve': Host('Eve')}

    network.delay = 0

    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    # B <-> E
    hosts['bob'].add_connection('Eve')
    hosts['eve'].add_connection('Bob')

    hosts['alice'].start()
    hosts['bob'].start()
    hosts['eve'].start()

    for h in hosts.values():
        network.add_host(h)

    q_id, _ = hosts['alice'].send_epr(hosts['eve'].host_id, await_ack=True)

    i = 0
    q1 = None
    q2 = None
    while i < MAX_WAIT and q1 is None:
        q1 = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)
        i += 1
        time.sleep(1)

    assert q1 is not None

    i = 0
    while i < MAX_WAIT and q2 is None:
        q2 = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)
        i += 1
        time.sleep(1)

    assert q2 is not None
    assert q1.measure() == q2.measure()
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
