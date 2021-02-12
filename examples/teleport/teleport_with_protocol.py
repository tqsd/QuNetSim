from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger

Logger.DISABLED = False


def sender_protocol(host: Host, receiver: str):
    q = Qubit(host)
    q.X()
    host.send_teleport(receiver, q, await_ack=False)


def receiver_protocol(host: Host, sender: str):
    q = host.get_data_qubit(sender, wait=10)
    print(f"{host.host_id} received qubit and measured the state {q.measure()}.")


def main():
    network = Network.get_instance()
    network.start()

    host_alice = Host('Alice')
    host_bob = Host('Bob')
    host_eve = Host('Eve')

    host_alice.add_connection('Bob')
    host_bob.add_connections(['Alice', 'Eve'])
    host_eve.add_connection('Bob')

    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    t1 = host_alice.run_protocol(sender_protocol, ('Eve',))
    t2 = host_eve.run_protocol(receiver_protocol, ('Alice',))

    t1.join()
    t2.join()
    network.stop(True)


if __name__ == '__main__':
    main()
