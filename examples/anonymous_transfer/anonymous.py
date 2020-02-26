import time

from components.host import Host
from components.network import Network
import random

from objects.qubit import Qubit


def distribute(host, nodes):
    # distribute=True => sender doesn't keep part of the GHZ
    host.send_ghz(nodes, distribute=True)


def sender(host, distributor, r, epr_id):
    q = host.get_ghz(distributor, wait=10)
    b = random.choice(['0', '1'])
    host.send_broadcast(b)
    if b == '1':
        q.Z()

    host.add_epr(r, q, q_id=epr_id)
    sending_qubit = Qubit(host)
    sending_qubit.X()
    print('Sending %s' % sending_qubit.id)
    # Generate EPR if none shouldn't change anything, but if there is
    # no shared entanglement between s and r, then there should
    # be a mistake in the protocol
    host.send_teleport(r, sending_qubit, generate_epr_if_none=False, await_ack=False)
    host.empty_classical()


def receiver(host, distributor, s, epr_id):
    q = host.get_ghz(distributor, wait=10)
    b = random.choice(['0', '1'])
    host.send_broadcast(b)

    messages = []
    # Await broadcast messages from all parties
    while len(messages) < 3:
        messages = host.classical
        time.sleep(0.5)

    print([m.content for m in messages])
    parity = int(b)
    for m in messages:
        if m.sender != s:
            parity = parity ^ int(m.content)

    if parity == 1:
        q.Z()

    print('established secret EPR')
    host.add_epr(s, q, q_id=epr_id)
    q = host.get_data_qubit(s, wait=10)
    host.empty_classical()
    print('Received qubit %s in the %d state' % (q.id, q.measure()))


def node(host, distributor):
    q = host.get_ghz(distributor, wait=10)
    if q is None:
        print('failed')
        return
    q.H()
    m = q.measure()
    host.send_broadcast(str(m))


def main():
    network = Network.get_instance()
    nodes = ['A', 'B', 'C', 'D', 'E']
    network.start(nodes)

    host_A = Host('A')
    host_A.add_connections(['B', 'C', 'D', 'E'])
    host_A.start()
    host_B = Host('B')
    host_B.add_connection('A')
    host_B.add_c_connections(['C', 'D', 'E'])
    host_B.start()
    host_C = Host('C')
    host_C.add_connection('A')
    host_C.add_c_connections(['B', 'D', 'E'])
    host_C.start()
    host_D = Host('D')
    host_D.add_connection('A')
    host_D.add_c_connections(['B', 'C', 'E'])
    host_D.start()
    host_E = Host('E')
    host_E.add_connection('A')
    host_E.add_c_connections(['B', 'C', 'D'])
    host_E.start()

    network.add_hosts([host_A, host_B, host_C, host_D, host_E])

    for i in range(10):
        # The ID of the generated secret EPR pair has to be agreed upon in advance
        epr_id = '123'
        host_D.run_protocol(sender, (host_A.host_id, host_E.host_id, epr_id))
        host_A.run_protocol(distribute, ([host_B.host_id, host_C.host_id, host_D.host_id, host_E.host_id],))
        host_B.run_protocol(node, (host_A.host_id,))
        host_C.run_protocol(node, (host_A.host_id,))
        host_E.run_protocol(receiver, (host_A.host_id, host_D.host_id, epr_id), blocking=True)
        time.sleep(0.5)
    network.stop(True)


if __name__ == '__main__':
    main()
