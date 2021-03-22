from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.backends import CQCBackend, ProjectQBackend, EQSNBackend, QuTipBackend
import pytest


def setup_network(num_hosts, backend):
    network = Network.get_instance()
    network.start(nodes=[str(i) for i in range(num_hosts)], backend=backend)
    network.delay = 0.0

    hosts = []
    for i in range(num_hosts):
        h = Host(str(i), backend=backend)
        h.delay = 0
        h.start()
        if i < num_hosts - 1:
            h.add_connection(str(i + 1))
        if i > 0:
            h.add_connection(str(i - 1))
        hosts.append(h)

    network.add_hosts(hosts)

    return network, hosts


def teleport(sender, receiver):
    for i in range(10):
        q1 = Qubit(sender)
        sender.send_teleport(receiver.host_id, q1, await_ack=False, no_ack=True)
        q2 = receiver.get_data_qubit(sender.host_id, q1.id, wait=-1)
        _ = q2.measure()


def superdense(sender, receiver):
    for i in range(10):
        sender.send_superdense(receiver.host_id, '11', await_ack=False, no_ack=True)
        _ = receiver.get_next_classical(sender.host_id, wait=-1)


def ghz(sender, receivers):
    ms = []
    for i in range(10):
        q_id = sender.send_ghz([receiver.host_id for receiver in receivers], await_ack=False, no_ack=True)
        m = []
        for receiver in receivers:
            q = receiver.get_ghz(sender.host_id, q_id, wait=20)
            m.append(q.measure())
        ms.append(m)
    return ms


@pytest.mark.cqc_super
def test_super_ten_hops_cqc(benchmark):
    backend = CQCBackend()
    network, hosts = setup_network(3, backend)
    benchmark.pedantic(superdense, args=(hosts[0], hosts[-1]), rounds=1)
    network.stop(True)


@pytest.mark.cqc_tele
def test_tele_ten_hops_cqc(benchmark):
    backend = CQCBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(teleport, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.cqc_ghz
def test_ghz_ten_hops_cqc(benchmark):
    backend = CQCBackend()
    nodes = 2
    network, hosts = setup_network(nodes, backend)
    ms = benchmark.pedantic(ghz, args=(hosts[0], hosts[1:]), rounds=1)
    for m in ms:
        assert (sum(m) == nodes - 1 or sum(m) == 0)
    network.stop(True)


@pytest.mark.pq_super
def test_super_ten_hops_pq(benchmark):
    backend = ProjectQBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(superdense, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.pq_tele
def test_teleport_ten_hops_pq(benchmark):
    backend = ProjectQBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(teleport, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.pq_ghz
def test_ghz_ten_nodes_pq(benchmark):
    backend = ProjectQBackend()
    nodes = 5
    network, hosts = setup_network(nodes, backend)
    ms = benchmark.pedantic(ghz, args=(hosts[0], hosts[1:]), rounds=1)
    for m in ms:
        assert (sum(m) == nodes - 1 or sum(m) == 0)
    network.stop(True)


@pytest.mark.eqsn_ghz
def test_ghz_ten_nodes(benchmark):
    backend = EQSNBackend()
    nodes = 10
    network, hosts = setup_network(nodes, backend)
    ms = benchmark.pedantic(ghz, args=(hosts[0], hosts[1:]), rounds=30)
    for m in ms:
        assert (sum(m) == nodes - 1 or sum(m) == 0)
    network.stop(True)


@pytest.mark.eqsn_tele
def test_teleport_ten_hops(benchmark):
    backend = EQSNBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(teleport, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.eqsn_super
def test_teleport_ten_hops(benchmark):
    backend = EQSNBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(superdense, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.qt_ghz
def test_ghz_ten_nodes_qt(benchmark):
    backend = QuTipBackend()
    nodes = 10
    network, hosts = setup_network(nodes, backend)
    ms = benchmark.pedantic(ghz, args=(hosts[0], hosts[1:]), rounds=30)
    for m in ms:
        assert (sum(m) == nodes - 1 or sum(m) == 0)
    network.stop(True)


@pytest.mark.qt_tele
def test_teleport_ten_hops_qt(benchmark):
    backend = QuTipBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(teleport, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)


@pytest.mark.qt_super
def test_teleport_ten_hops_qt(benchmark):
    backend = QuTipBackend()
    network, hosts = setup_network(11, backend)
    benchmark.pedantic(superdense, args=(hosts[0], hosts[-1]), rounds=30)
    network.stop(True)
