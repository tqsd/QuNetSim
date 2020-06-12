import sys
import time

sys.path.append("../..")
from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects.qubit import Qubit

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

    q = Qubit(hosts['alice'])
    q.X()

    q_id = hosts['alice'].send_epr(hosts['eve'].host_id)

    # TODO: Why do we need this to pass the test?
    time.sleep(6)

    hosts['alice'].send_teleport(hosts['eve'].host_id, q)

    q1_epr = None
    q2_epr = None
    q_teleport = None

    i = 0
    while q1_epr is None and i < MAX_WAIT:
        q1_epr = hosts['alice'].get_epr(hosts['eve'].host_id, q_id)
        if q1_epr is not None:
            q1_epr = q1_epr
        i += 1
        time.sleep(1)

    i = 0
    while q2_epr is None and i < MAX_WAIT:
        q2_epr = hosts['eve'].get_epr(hosts['alice'].host_id, q_id)
        if q2_epr is not None:
            q2_epr = q2_epr
        i += 1
        time.sleep(1)

    i = 0
    while q_teleport is None and i < MAX_WAIT:
        q_teleport = hosts['eve'].get_data_qubit(hosts['alice'].host_id)
        if q_teleport is not None:
            q_teleport = q_teleport
        i += 1
        time.sleep(1)

    assert q1_epr is not None
    assert q2_epr is not None
    assert q_teleport is not None
    assert q1_epr.measure() == q2_epr.measure()
    assert(q_teleport.measure() == 1)
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
