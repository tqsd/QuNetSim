from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit

MAX_WAIT = 20

def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    backend = CQCBackend()
    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend),
             'eve': Host('Eve', backend)}

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

    network.use_hop_by_hop = False
    hosts['alice'].send_classical(hosts['eve'].host_id, 'testing123')

    i = 0
    messages = hosts['eve'].classical
    while i < MAX_WAIT and len(messages) == 0:
        messages = hosts['eve'].classical
        i += 1
        time.sleep(1)

    assert len(messages) > 0
    assert messages[0].sender == hosts['alice'].host_id
    assert messages[0].content == 'testing123'
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
