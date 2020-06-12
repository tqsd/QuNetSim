from qunetsim import components as protocols
from qunetsim.components import Network
from qunetsim.components import Host
from qunetsim.backends import EQSNBackend


def main():
    backend = EQSNBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.7

    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    network.delay = 0
    # A <-> B
    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    # send messages to Bob without waiting for ACKs
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob one', await_ack=False)
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob two', await_ack=False)
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob three', await_ack=False)
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob four', await_ack=False)

    # Wait for all Acks from Bob
    hosts['alice'].await_remaining_acks(hosts['bob'].host_id)

    saw_ack = [False, False, False, False]
    messages = hosts['alice'].classical
    for m in messages:
        if m.content == protocols.ACK:
            saw_ack[m.seq_num] = True

    for ack in saw_ack:
        assert ack
    print("All tests succesfull!")
    network.stop(True)


if __name__ == '__main__':
    print("Test outdated")
    exit(0)
    main()
