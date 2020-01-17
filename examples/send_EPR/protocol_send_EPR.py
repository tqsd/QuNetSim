from components.host import Host
from components.network import Network
import time


def protocol_1(host, receiver):
    # Here we write the protocol code for a host.
    epr_id, _ = host.send_epr(receiver, await_ack=True)
    q = host.get_epr(receiver, q_id=epr_id)
    print('Host 1 measured: %d' % q.measure())


def protocol_2(host, sender):
    # Here we write the protocol code for another host.

    # Host 2 waits 5 seconds for the EPR to arrive.
    q = host.get_epr(sender, wait=5)
    assert q is not None
    print('Host 2 measured: %d' % q.measure())


def main():
    network = Network.get_instance()
    nodes = ['A', 'B', 'C']
    network.start(nodes)

    host_A = Host('A')
    host_A.add_connection('B')
    host_A.add_connection('C')
    host_A.start()
    host_B = Host('B')
    host_B.add_connection('A')
    host_B.add_connection('C')
    host_B.start()
    host_C = Host('C')
    host_C.add_connection('A')
    host_C.add_connection('B')
    host_C.start()

    network.add_host(host_A)
    network.add_host(host_B)
    network.add_host(host_C)

    host_A.run_protocol(protocol_1, (host_C.host_id,))
    host_C.run_protocol(protocol_2, (host_A.host_id,))


if __name__ == '__main__':
    main()
