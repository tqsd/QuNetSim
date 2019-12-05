from cqc.pythonLib import CQCConnection
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.7

    print('')

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob, CQCConnection('Eve') as Eve, CQCConnection(
            'Dean') as Dean:
        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000000')
        host_bob.add_connection('00000011')
        host_bob.start()

        host_eve = Host('00000011', Eve)
        host_eve.add_connection('00000001')
        host_eve.add_connection('00000111')
        host_eve.start()

        host_dean = Host('00000111', Dean)
        host_dean.add_connection('00000011')
        host_dean.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)
        network.add_host(host_dean)

        q_id1 = host_alice.send_epr('00000011')
        time.sleep(15)

        q1 = host_alice.get_epr('00000011', q_id1)['q']
        q2 = host_eve.get_epr('00000000', q_id1)['q']

        if q1 is not None and q2 is not None:
            m1 = q1.measure()
            m2 = q2.measure()

            print("Results of the measurements for q_id1 are ")
            print(m1)
            print(m2)
        else:
            print('failed')

        start_time = time.time()
        while time.time() - start_time < 20:
            pass

        network.stop(True)
        exit()


if __name__ == '__main__':
    main()
