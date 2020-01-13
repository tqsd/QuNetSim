from simulaqron.network import Network as SimulaNetwork
from simulaqron.settings import simulaqron_settings

import sys
import time

sys.path.append("../..")
from backends.cqc_backend import CQCBackend
from components.host import Host
from components.network import Network
from objects.qubit import Qubit


def main():

    network = Network.get_instance()
    backend = CQCBackend()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.5


    host_alice = Host('Alice', backend)
    host_bob = Host('Bob', backend)

    host_alice.add_connection('Bob')
    host_bob.add_connection('Alice')

    host_alice.start()
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_bob)

    q1 = Qubit(host_alice)
    q1.X()

    q_id = host_alice.send_teleport('Bob', q1)
    time.sleep(10)

    q = host_bob.get_data_qubit(host_alice.host_id, q_id)
    assert q is not None
    print(q.measure())

    start_time = time.time()

    while time.time() - start_time < 5:
        pass

    network.stop(True)

if __name__ == '__main__':
    main()
