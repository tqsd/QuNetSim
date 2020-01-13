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

    network.delay = 0

    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    hosts['alice'].send_classical(hosts['bob'].host_id, 'Hello Bob', False)
    hosts['bob'].send_classical(hosts['alice'].host_id, 'Hello Alice', False)

    i = 0
    bob_messages = hosts['bob'].classical
    while i < 5 and len(bob_messages) == 0:
        bob_messages = hosts['bob'].classical
        i += 1
        time.sleep(1)

    i = 0
    alice_messages = hosts['alice'].classical
    while i < 5 and len(alice_messages) == 0:
        alice_messages = hosts['alice'].classical
        i += 1
        time.sleep(1)

    assert len(alice_messages) > 0
    assert alice_messages[0].sender == hosts['bob'].host_id
    assert alice_messages[0].content == 'Hello Alice'

    assert (len(bob_messages) > 0)
    assert (bob_messages[0].sender == hosts['alice'].host_id)
    assert (bob_messages[0].content == 'Hello Bob')
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
