from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()

    print('')

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob, CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:
        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)
        host_eve.add_connection('00000111')
        host_eve.start()

        host_dean = Host('00000111', Dean)
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        host_alice.send_epr('00000111')

        time.sleep(15)

        q1 = host_alice.get_epr('00000111')
        q2 = host_dean.get_epr('00000000')

        m1 = q1.measure()
        m2 = q2.measure()

        print("Results of the measurements are " )
        print(m1)
        print(m2)



        nodes = [host_alice, host_bob, host_eve, host_dean]

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        for h in nodes:
            h.stop()


main()
