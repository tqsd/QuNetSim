from simulaqron.network import Network as SimulaNetwork
from simulaqron.settings import simulaqron_settings

from cqc.pythonLib import CQCConnection, qubit

import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():

    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.5

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:

        host_alice = Host('00000000', Alice)
        host_bob = Host('00000001', Bob)

        host_alice.add_connection('00000001')
        host_bob.add_connection('00000000')

        host_alice.start()
        host_bob.start()

        network.add_host(host_alice)
        network.add_host(host_bob)

        q1 = qubit(Alice)
        q1.X()

        q_id = host_alice.send_teleport('00000001', q1)
        time.sleep(10)

        q = host_bob.get_data_qubit(host_alice.host_id, q_id)
        assert q is not None
        print(q['q'].measure())

        start_time = time.time()

        while time.time() - start_time < 5:
            pass

        network.stop(True)

if __name__ == '__main__':
    main()
