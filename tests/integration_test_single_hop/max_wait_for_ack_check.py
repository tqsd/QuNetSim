from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.backends import EQSNBackend


def main():
    backend = EQSNBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.0

    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    ack_received_1 = hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob one', await_ack=True)
    hosts['alice'].max_ack_wait = 0.0
    ack_received_2 = hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob one', await_ack=True)
    assert ack_received_1
    assert not ack_received_2
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
