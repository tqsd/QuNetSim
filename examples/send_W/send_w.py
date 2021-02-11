from qunetsim.backends import EQSNBackend
from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Logger

Logger.DISABLED = False


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    back = EQSNBackend()
    network.start(nodes, back)

    network.delay = 0.1

    host_alice = Host('Alice', back)
    host_alice.add_connection('Bob')
    host_alice.add_connection('Eve')
    host_alice.start()

    host_bob = Host('Bob', back)
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve', back)
    host_eve.add_connection('Bob')
    host_eve.add_connection('Dean')
    host_eve.add_connection('Alice')
    host_eve.start()

    host_dean = Host('Dean', back)
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)

    share_list = ["Bob", "Eve", "Dean"]
    q_id1, ack_received = host_alice.send_w(share_list, await_ack=True)

    print("Alice received ACK from all? " + str(ack_received))

    q1 = host_alice.get_w('Alice', q_id1, wait=10)
    q2 = host_bob.get_w('Alice', q_id1, wait=10)
    q3 = host_eve.get_w('Alice', q_id1, wait=10)
    q4 = host_dean.get_w('Alice', q_id1, wait=10)

    m1 = q1.measure()
    m2 = q2.measure()
    m3 = q3.measure()
    m4 = q4.measure()

    print("\nResults of measurements are %d, %d, %d, %d." % (m1, m2, m3, m4))

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
