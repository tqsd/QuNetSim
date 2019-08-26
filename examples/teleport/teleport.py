from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger


def main():
    network = Network.get_instance()
    logger = Logger.get_instance()
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve:
        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)
        host_eve.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        q1 = qubit(Alice)
        q1.X()

        q2 = qubit(Alice)
        q3 = qubit(Alice)

        q2.H()
        q2.cnot(q3)

        host_alice.send_epr('00000011')
        host_alice.send_epr('00000011')
        host_alice.send_epr('00000011')

        time.sleep(0.5)

        host_alice.send_teleport('00000011', q1)
        host_alice.send_teleport('00000011', q2)
        host_alice.send_teleport('00000011', q3)

        nodes = [host_alice, host_bob, host_eve]

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        for h in nodes:
            h.stop()


main()
