from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit


def setup_network():
    network = Network.get_instance()
    network.start()
    network.delay = 0.0
    host_A = Host('A')
    host_A.add_connection('B')
    host_A.delay = 0
    host_A.start()

    host_B = Host('B')
    host_B.add_connection('C')
    host_B.add_connection('A')
    host_B.delay = 0
    host_B.start()

    host_C = Host('C')
    host_C.add_connection('B')
    host_C.delay = 0
    host_C.start()

    network.add_host(host_A)
    network.add_host(host_B)
    network.add_host(host_C)

    return network, host_A, host_B, host_C


def test_teleport(benchmark):

    def teleport(network, host_A, host_B, host_C):
        q = Qubit(host_A)
        host_A.send_teleport(host_C.host_id, q, await_ack=True)
        q_C = host_C.get_data_qubit(host_A.host_id, q.id)
        _ = q_C.measure()

    network, host_A, host_B, host_C = setup_network()
    benchmark(teleport, network, host_A, host_B, host_C)
    network.stop(True)


def test_superdense(benchmark):

    def superdense(network, host_A, host_B, host_C):
        host_A.send_superdense(host_C.host_id, '11', await_ack=True)
        msg = host_C.get_next_classical(host_A.host_id)
        return msg

    network, host_A, host_B, host_C = setup_network()
    msg = benchmark(superdense, network, host_A, host_B, host_C)
    assert msg.content == '11'
    network.stop(True)


def test_key_distribution(benchmark):
    key_size = 8

    def key_distribution(network, host_A, host_B, host_C):
        host_A.send_key(host_C.host_id, key_size)
        key1, _ = host_A.get_key(host_C.host_id)
        key2, _ = host_C.get_key(host_A.host_id)
        return key1, key2

    network, host_A, host_B, host_C = setup_network()
    key1, key2 = benchmark(key_distribution, network, host_A, host_B, host_C)
    assert key1 == key2
    network.stop(True)
