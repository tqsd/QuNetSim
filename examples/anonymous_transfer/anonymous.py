import time

from backends.projectq_backend import ProjectQBackend
from components.host import Host
from components.network import Network
from components.logger import Logger
import random

from objects.qubit import Qubit


def distribute(host, nodes):
    host.send_ghz(nodes)


def sender(host, distributor, r):
    q = host.get_ghz(distributor, wait=5)
    b = random.choice(['0', '1'])
    host.send_broadcast(b)
    if b == '1':
        q.Z()

    host.add_epr(r, q, q_id='1')
    sending_qubit = Qubit(host)
    sending_qubit.I()
    print('Sending %s' % sending_qubit.id)
    host.send_teleport(r, sending_qubit, generate_epr_if_none=False)


def receiver(host, distributor, s):
    q = host.get_ghz(distributor, wait=5)
    b = random.choice(['0', '1'])
    host.send_broadcast(b)

    messages = []
    while len(messages) < 3:
        messages = host.classical
        time.sleep(0.5)

    print([m.content for m in messages])
    parity = int(b)
    for m in messages:
        parity = parity ^ int(m.content)

    if parity == 1:
        q.Z()

    print('established secret EPR')
    host.add_epr(s, q, q_id='1')
    q = host.get_data_qubit(s, wait=5)
    print('Received qubit %s in the %d state' % (q.id, q.measure()))


def node(host, distributor):
    q = host.get_ghz(distributor, wait=5)
    if q is None:
        print('failed')
        return
    q.H()
    m = q.measure()
    host.send_broadcast(str(m))


def main():
    network = Network.get_instance()
    nodes = ['A', 'B', 'C', 'D', 'E']
    backend = ProjectQBackend()
    network.start(nodes, backend)

    network.delay = 0.2

    host_A = Host('A', backend)
    host_A.add_connections(['B', 'C', 'D', 'E'])
    host_A.start()
    host_B = Host('B', backend)
    host_B.add_connection('A')
    host_B.add_c_connections(['C', 'D', 'E'])
    host_B.start()
    host_C = Host('C', backend)
    host_C.add_connection('A')
    host_C.add_c_connections(['B', 'D', 'E'])
    host_C.start()
    host_D = Host('D', backend)
    host_D.add_connection('A')
    host_D.add_c_connections(['B', 'C', 'E'])
    host_D.start()
    host_E = Host('E', backend)
    host_E.add_connection('A')
    host_E.add_c_connections(['B', 'C', 'D'])
    host_E.start()

    network.add_host(host_A)
    network.add_host(host_B)
    network.add_host(host_C)
    network.add_host(host_D)
    network.add_host(host_E)

    threads = []
    threads.append(host_D.run_protocol(sender, (host_A.host_id, host_E.host_id)))
    threads.append(host_E.run_protocol(receiver, (host_A.host_id, host_D.host_id)))
    threads.append(host_A.run_protocol(distribute, ([host_B.host_id, host_C.host_id, host_D.host_id, host_E.host_id],)))
    threads.append(host_B.run_protocol(node, ('A',)))
    threads.append(host_C.run_protocol(node, ('A',)))

    for t in threads:
        t.join()

    network.stop(True)


if __name__ == '__main__':
    main()
