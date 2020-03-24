from components.host import Host
from components.network import Network
from backends.eqsn_backend import EQSNBackend


def main():
    backend = EQSNBackend()
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes, backend)
    network.delay = 0.0

    hosts = {'alice': Host('Alice', backend),
             'bob': Host('Bob', backend)}

    network.start(nodes, backend)
    network.packet_drop_rate = 0.5
    network.delay = 0

    hosts['alice'].add_connection('Bob')
    hosts['bob'].add_connection('Alice')

    hosts['alice'].start()
    hosts['bob'].start()

    for h in hosts.values():
        network.add_host(h)

    # ACKs for 1 hop take at most 2 seconds
    hosts['alice'].max_ack_wait = 0.5
    num_acks = 0
    # don't make more then 10 attempts, since of receiver window.
    num_messages = 20
    for _ in range(num_messages):
        ack = hosts['alice'].send_classical(
            hosts['bob'].host_id, 'Hello Bob', await_ack=True)
        if ack:
            num_acks += 1

    num_messages_bob_received = len(hosts['bob'].classical)
    assert num_acks != num_messages
    assert num_acks < num_messages
    assert num_messages_bob_received < num_messages

    # ACKs can also get dropped
    assert num_messages_bob_received > num_acks
    assert float(num_acks) / num_messages < 0.9
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
