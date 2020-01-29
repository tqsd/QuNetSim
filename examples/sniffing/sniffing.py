from components.host import Host
from components.network import Network
from objects.qubit import Qubit

amount_transmit = 10

def Alice(host):
    for _ in range(amount_transmit):
        q = Qubit(host)
        q.H()
        print("Alice prepared a qubit 0 in Hadamard basis.")
        host.send_qubit('Eve', q, await_ack=True)

def Bob_sniffing_quantum(qubit, from_host):
    m = qubit.measure(non_destructive=True)
    print("Bob measured sniffed qubit and measured %d." % m)

def Bob_sniffing_classical():
    pass

def Eve(host):
    for _ in range(amount_transmit):
        q = host.get_data_qubit('Alice', wait=10)
        q.H()
        m = q.measure()
        print("Eve measured %d." % m)


def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve"]
    network.start(nodes)
    network.delay = 0.1

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.start()


    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    host_bob.quantum_relay_sniffing = True
    host_bob.quantum_relay_sniffing_function = Bob_sniffing_quantum

    t1 = host_alice.run_protocol(Alice)
    t2 = host_eve.run_protocol(Eve)

    t1.join()
    t2.join()

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
