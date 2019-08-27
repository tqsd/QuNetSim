from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob, CQCConnection('Eve') as Eve:

        # q = qubit(Alice)
        # print(q)
        #
        # Alice.sendQubit(q, 'Bob');
        # q = Bob.recvQubit()
        # print(q)
        #
        # Bob.sendQubit(q, 'Eve')
        # q = Eve.recvQubit()
        # print(q)

        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)
        # host_eve.add_connection('00000111')
        host_eve.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        host_alice.send_superdense('00000011', '11')
        host_alice.send_superdense('00000011', '10')
        host_alice.send_superdense('00000011', '01')
        # host_alice.send_superdense('00000011', '00')
        # host_alice.send_superdense('00000011', '11')
        # host_alice.send_superdense('00000011', '10')

        host_alice.send_superdense('00000001', '11')
        host_alice.send_superdense('00000001', '10')

        nodes = [host_alice, host_bob, host_eve]

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        for h in nodes:
            h.stop()


main()
