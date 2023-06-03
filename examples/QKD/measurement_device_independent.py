import random
from enum import StrEnum, auto
from dataclasses import dataclass
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger

Logger.DISABLED = True
default_key_len = 32
default_batch_len = 8


class Basis(StrEnum):
    rect = auto()
    diag = auto()


@dataclass()
class BB84State():
    basis: Basis
    value: int

    def into_qubit(self, host: Host) -> Qubit:
        q = Qubit(host)

        if self.value == 1:
            q.X()
        if self.basis == Basis.diag:
            q.H()

        return q


class _BB84StateSpace():
    states = [BB84State(basis=b, value=v)
              for b in (Basis.diag, Basis.rect)
              for v in (0, 1)]

    def __len__(self):
        return len(self.states)

    def __getitem__(self, i):
        return self.states[i]


# Treat this as a singleton.
BB84StateSpace = _BB84StateSpace()


# Helper class for Bell states in the computational basis
class RelayMessage(StrEnum):
    phi_minus = auto()
    phi_plus = auto()
    psi_plus = auto()
    psi_minus = auto()

    @staticmethod
    def from_measurement(x):
        m = {
            (0, 0): RelayMessage.phi_plus,
            (1, 0): RelayMessage.phi_minus,
            (0, 1): RelayMessage.psi_plus,
            (1, 1): RelayMessage.psi_minus,
        }
        return m[x]


@dataclass()
class MDIRelay():
    node: Host
    alice: Host
    bob: Host

    batch_len: int

    def measure(a: Qubit, b: Qubit):
        """
        Perform a Bell measurement on the given qubit pair and return the
        result, encoded as a RelayMessage.
        """

        a.cnot(b)
        a.H()
        m = (a.measure(), b.measure())
        return RelayMessage.from_measurement(m)

    def protocol(self, charlie):
        # collect qubits, measure, broadcast results
        while True:
            a, b, m = [], [], []
            for k in range(self.batch_len):
                a.append(charlie.get_qubit(self.alice.host_id, wait=-1))
                b.append(charlie.get_qubit(self.bob.host_id, wait=-1))
                m.append(MDIRelay.measure(a[k], b[k]))

            charlie.send_broadcast(" ".join(m))

    def run(self):
        return self.node.run_protocol(self.protocol)


@dataclass()
class MDINode():
    node: Host
    peer: Host
    relay: Host
    flip: bool

    key_len: int
    batch_len: int

    def protocol(self, node):
        key = []

        while True:
            print(f"key_{node.host_id:5} = {key[:self.key_len]}")
            if len(key) >= self.key_len:
                return

            # Quantum communication phase. Gather a batch of qubits and send
            # them to the relay.
            states, qbits = [], []
            for k in range(self.batch_len):
                states.append(random.choice(BB84StateSpace))
                qbits.append(states[k].into_qubit(node))

            for q in qbits:
                node.send_qubit(self.relay.host_id, q, await_ack=True)

            # Classical communication phase.
            msg = node.get_next_classical(self.relay.host_id)
            measurements = msg.content.split()

            # Post selection
            # Find states that led to successful measurements.
            good_states = []
            good_measurements = []
            for k, (s, m) in enumerate(zip(states, measurements)):
                if m in {RelayMessage.psi_plus, RelayMessage.psi_minus}:
                    good_states.append(s)
                    good_measurements.append(m)

            # Send peer our basis sequence for successful measurements.
            node.send_classical(self.peer.host_id,
                                " ".join([s.basis for s in good_states]))

            # Post² selection: select the bits where node and peer used the
            # same basis.
            msg = node.get_next_classical(self.peer.host_id)
            peer_bases = msg.content.split()

            for k in range(len(good_measurements)):
                if good_states[k].basis == peer_bases[k]:
                    key.append(good_states[k].value)

                    if self.flip and not (
                        good_measurements[k] == RelayMessage.psi_plus
                        and good_states[k].basis == Basis.diag
                    ):
                        key[-1] ^= 1

    def run(self):
        return self.node.run_protocol(self.protocol)


@dataclass(init=False)
class MDINetwork():
    alice:   MDINode
    bob:     MDINode
    charlie: MDIRelay
    network: Network

    def __init__(self, key_len=default_key_len,
                 batch_len=default_batch_len):
        self.network = Network.get_instance()
        nodes = ['Alice', 'Bob', 'Charlie']
        self.network.start(nodes)

        alice = Host('Alice')
        bob = Host('Bob')
        charlie = Host('Charlie')

        alice.add_connections(['Bob', 'Charlie'])
        bob.add_connections(['Alice', 'Charlie'])
        charlie.add_connections(['Alice', 'Bob'])

        self.network.delay = 0.1
        bob.start()
        alice.start()
        self.network.delay = 0.2
        charlie.start()

        self.network.add_host(alice)
        self.network.add_host(bob)
        self.network.add_host(charlie)

        self.alice = MDINode(node=alice, peer=bob, relay=charlie,
                             flip=False, key_len=key_len, batch_len=batch_len)
        self.bob = MDINode(node=bob, peer=alice, relay=charlie,
                           flip=True, key_len=key_len, batch_len=batch_len)
        self.charlie = MDIRelay(node=charlie,
                                alice=alice, bob=bob, batch_len=batch_len)

    def simulate(self):
        t1 = self.alice.run()
        t2 = self.bob.run()
        _ = self.charlie.run()

        t1.join()
        t2.join()
        self.network.stop(True)


def main():
    random.seed(2**2023)
    MDINetwork().simulate()

    exit()


if __name__ == '__main__':
    main()
