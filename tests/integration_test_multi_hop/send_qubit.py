import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network
from objects.qubit import Qubit

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
    q_id = hosts['alice'].send_qubit(hosts['eve'].host_id, q)

    i = 0
    q1 = None
    while i < MAX_WAIT and q1 is None:
        q1 = hosts['eve'].get_data_qubit(hosts['alice'].host_id, q_id)
        i += 1
        time.sleep(1)

    assert q1 != None
    assert q1.measure() == 1


    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
