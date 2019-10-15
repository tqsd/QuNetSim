from simulaqron.network import Network as SimulaNetwork
from simulaqron.settings import simulaqron_settings

from cqc.pythonLib import CQCConnection, qubit

import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    # nodes = ["Bob", "Alice"]
    # sim_network = SimulaNetwork(nodes=nodes, force=True)
    # sim_network.start()

    # time.sleep(1)

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob:

        network = Network.get_instance()
        network.start()
        print('')

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

        q_id = host_alice.send_qubit('00000001', q1)

        time.sleep(10)

        q = host_bob.get_data_qubit(host_alice.host_id, q_id)
        assert q is not None
        print(q.measure())

        nodes = [host_alice, host_bob]
        start_time = time.time()

        while time.time() - start_time < 5:
            pass

        for h in nodes:
            h.stop()
        network.stop()

        # sim_network.stop()
        # simulaqron_settings.default_settings()


if __name__ == '__main__':
    main()
