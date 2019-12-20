from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.7
    backend = CQCBackend()
    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    hosts['alice'].send_superdense(hosts['bob'].host_id, '11')

    messages = hosts['bob'].classical
    i = 0
    while i < 5 and len(messages) == 0:
        messages = hosts['bob'].classical
        i += 1
        time.sleep(1)

    q = Qubit(hosts['alice'])
    q.X()

    hosts['alice'].send_teleport(hosts['bob'].host_id, q)
    q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
    i = 0
    while q2 is None and i < 5:
        q2 = hosts['bob'].get_data_qubit(hosts['alice'].host_id)
        i += 1
        time.sleep(1)

    assert messages != None
    assert len(messages) > 0
    assert (messages[0]['sender'] == hosts['alice'].host_id)
    assert (messages[0]['message'] == '11')

    assert q2 != None
    assert (q2.measure() == 1)
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
