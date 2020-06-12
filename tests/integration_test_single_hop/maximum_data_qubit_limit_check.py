import sys
import time

sys.path.append("../..")
from qunetsim.backends import CQCBackend
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit


def main():
    print("Test maximum data qubit has been skipped.")
    return
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

    hosts['alice'].memory_limit = 1
    hosts['bob'].memory_limit = 1

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    q_alice_id_1 = hosts['alice'].send_qubit(hosts['bob'].host_id, Qubit(hosts['alice']))
    time.sleep(2)
    q_alice_id_2 = hosts['alice'].send_qubit(hosts['bob'].host_id, Qubit(hosts['alice']))
    time.sleep(2)

    q_bob_id_1 = hosts['bob'].send_qubit(hosts['alice'].host_id, Qubit(hosts['bob']))
    time.sleep(2)
    q_bob_id_2 = hosts['bob'].send_qubit(hosts['alice'].host_id, Qubit(hosts['bob']))
    time.sleep(2)

    # Allow the network to process the requests
    # TODO: remove the need for this
    time.sleep(2)

    i = 0
    while len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) < 1 and i < 5:
        time.sleep(1)
        i += 1

    i = 0
    while len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) < 1 and i < 5:
        time.sleep(1)
        i += 1

    assert len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 1
    assert hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_1).measure() == 0
    assert hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_2) == None
    assert len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 1
    assert hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_1).measure() == 0
    assert hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_2) == None

    hosts['alice'].set_data_qubit_memory_limit(2, hosts['bob'].host_id)
    hosts['bob'].set_data_qubit_memory_limit(2)

    q_alice_id_1 = hosts['alice'].send_qubit(hosts['bob'].host_id, Qubit(hosts['alice']))
    time.sleep(2)
    q_alice_id_2 = hosts['alice'].send_qubit(hosts['bob'].host_id, Qubit(hosts['alice']))
    time.sleep(2)
    q_alice_id_3 = hosts['alice'].send_qubit(hosts['bob'].host_id, Qubit(hosts['alice']))
    time.sleep(2)

    q_bob_id_1 = hosts['bob'].send_qubit(hosts['alice'].host_id, Qubit(hosts['bob']))
    time.sleep(2)
    q_bob_id_2 = hosts['bob'].send_qubit(hosts['alice'].host_id, Qubit(hosts['bob']))
    time.sleep(2)
    q_bob_id_3 = hosts['bob'].send_qubit(hosts['alice'].host_id, Qubit(hosts['bob']))
    time.sleep(2)

    # Allow the network to process the requests
    time.sleep(3)

    i = 0
    while len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) < 2 and i < 5:
        time.sleep(1)
        i += 1

    i = 0
    while len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) < 2 and i < 5:
        time.sleep(1)
        i += 1

    assert len(hosts['alice'].get_data_qubits(hosts['bob'].host_id)) == 2
    assert hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_1).measure() == 0
    assert hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_2).measure() == 0
    assert hosts['alice'].get_data_qubit(hosts['bob'].host_id, q_bob_id_3) == None

    assert len(hosts['bob'].get_data_qubits(hosts['alice'].host_id)) == 2
    assert hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_1).measure() == 0
    assert hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_2).measure() == 0
    assert hosts['bob'].get_data_qubit(hosts['alice'].host_id, q_alice_id_3) == None
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
