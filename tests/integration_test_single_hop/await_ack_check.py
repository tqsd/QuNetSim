from qunetsim import components as protocols
from qunetsim.components.network import Network
from qunetsim.components.host import Host
from qunetsim.backends import CQCBackend


def main():
    print("Skip test, this test has to be updated!")
    return
    backend = CQCBackend()
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

    # print(f"ack test - SEND CLASSICAL - started at {time.strftime('%X')}")
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob one', await_ack=True)
    hosts['alice'].send_classical(
        hosts['bob'].host_id, 'hello bob two', await_ack=True)
    # print(f"ack test - SEND CLASSICAL - finished at {time.strftime('%X')}")

    saw_ack_1 = False
    saw_ack_2 = False
    messages = hosts['alice'].classical
    # print([m.seq_num for m in messages])
    for m in messages:
        if m.content == Constants.ACK and m.seq_num == 0:
            saw_ack_1 = True
        if m.content == Constants.ACK and m.seq_num == 1:
            saw_ack_2 = True
        if saw_ack_1 and saw_ack_2:
            break

    assert saw_ack_1
    assert saw_ack_2
    print("All tests succesfull!")
    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
