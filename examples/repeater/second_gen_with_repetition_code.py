from dataclasses import dataclass
from statistics import mode

from qunetsim.components import Host
from qunetsim.objects import Logger, Qubit
from qunetsim.components import Network

Logger.DISABLED = True


@dataclass()
class Ebit:
    val: tuple[int, int]

    def __str__(self):
        return {
            (0, 0): "phi+",
            (0, 1): "psi+",
            (1, 0): "phi-",
            (1, 1): "psi-",
        }[self.val]

    @staticmethod
    def from_bell_measurement(a: Qubit, b: Qubit):
        a.cnot(b)
        a.H()
        x = a.measure()
        y = b.measure()
        return Ebit((x, y))


def send_epr(host, peer):
    a, b = Qubit(host), Qubit(host)
    a.H()
    a.cnot(b)
    host.send_qubit(peer.host_id, b)
    return a


@dataclass(init=False)
class RepetitionCodedQubit:
    physical: list[Qubit]
    code_length: int

    def __init__(self, h: Host, code_length: int = 3):
        self.code_length = code_length
        self.physical = [Qubit(h) for _ in range(code_length)]

    def __getitem__(self, index):
        return self.physical[index]

    def H(self):  # this maps ⌈|0>⌋ to ⌈|+>⌋
        self.physical[0].H()
        for k in range(1, self.code_length):
            self.physical[0].cnot(self.physical[k])


# This circuit is from https://arxiv.org/pdf/quant-ph/0002039.pdf, page 9. It
# lets two peers perform a remote CNOT using a single EPR pair.
@dataclass()
class RemoteCNOT:
    """
    RemoteCNOT teleports qubits, |alpha> and |beta>, through an EPR pair
    composed of |red> and |blue>. The result of the protocol is that
        |red>  = |alpha>
        |blue> = |beta ⊕ alpha>
    """
    left: Host
    right: Host

    def left_protocol(self, alpha: Qubit, red: Qubit):
        red.cnot(alpha)
        x = alpha.measure()
        if x == 1:
            red.X()
        self.left.send_classical(self.right.host_id, str(x), await_ack=True)

        z = self.left.get_next_classical(self.right.host_id, wait=-1).content
        if z == '1':
            red.Z()

    def right_protocol(self, blue: Qubit, beta: Qubit):
        beta.cnot(blue)
        beta.H()

        x = self.right.get_next_classical(self.left.host_id, wait=-1).content
        if x == '1':
            blue.X()

        z = beta.measure()
        self.right.send_classical(self.left.host_id, str(z), await_ack=True)
        if z == 1:
            blue.Z()


@dataclass(init=False)
class EncodedGenerationProtocol:
    """
    EncodedGenerationProtocol establishes an encoded Φ^+ between left and right
    hosts. This is done as follows.

    1. locally prepare encoded states ⌈|+>⌋ and ⌈|0>⌋

    For each each physical qubit:

    2. left creates an EPR pair
    3. left distributes half of the EPR pair to right
    4. peers use the EPR pair to perform a transverse teleportation-based CNOT
    """
    left: Host
    right: Host
    remote_cnot: RemoteCNOT
    code_length: int

    def __init__(self, left, right, code_length=3):
        self.left = left
        self.right = right
        self.remote_cnot = RemoteCNOT(left, right)
        self.code_length = code_length

    def left_protocol(self, left: Host, n: int):
        logical = RepetitionCodedQubit(self.left, self.code_length)
        logical.H()

        for k, physical in enumerate(logical):
            epr = send_epr(self.left, self.right)
            self.remote_cnot.left_protocol(physical, epr)
            self.left.add_qubit(self.left.host_id, epr, f"{n}>{k}")

    def right_protocol(self, right: Host, n: int):
        # prepare an encoded |0>
        logical = RepetitionCodedQubit(right, self.code_length)

        out = []
        for k, physical in enumerate(logical):
            epr = self.right.get_qubit(self.left.host_id, wait=-1)
            self.remote_cnot.right_protocol(epr, physical)
            right.add_qubit(right.host_id, epr, f"{n}<{k}")
            out.append(epr)


def encoded_connection(host: Host, left: Host, right: Host, logical_qubit: int,
                       code_length: int = 3):
    """
    Perform transverse measurements of the code block for logical_qubit in the
    Bell basis.

    The logical measurement result is the mode of the physical measurement
    results.

    The logical measurement result is sent to the repeater's neighbours, hosts
    `left` and `right`.
    """
    ms = []
    for k in range(code_length):
        p = host.get_qubit_by_id(f"{logical_qubit}>{k}")
        q = host.get_qubit_by_id(f"{logical_qubit}<{k}")
        ms.append(str(Ebit.from_bell_measurement(p, q)))
    host.send_classical(left.host_id, mode(ms), await_ack=True)
    host.send_classical(right.host_id, mode(ms), await_ack=True)


def pauli_frame_left(host: Host, right: Host, n: int, code_length: int = 3):
    msg = host.get_next_classical(right.host_id, wait=-1).content
    for k in range(code_length):
        q = host.get_qubit_by_id(f"{n}>{k}")
        if msg == 'psi+':
            q.X()
        elif msg == 'phi-':
            q.Z()


def pauli_frame_right(host: Host, left: Host, logical_qubit: int,
                      code_length: int = 3):
    msg = host.get_next_classical(left.host_id, wait=-1).content
    for k in range(code_length):
        q = host.get_qubit_by_id(f"{logical_qubit}<{k}")
        if msg == 'psi-':
            q.Y()


def pretty_print_logical_qubit(h, n, code_length, left_side=True):
    if n > 0:
        print('|', end='')
    for k in range(code_length):
        if left_side:
            p = h.get_qubit_by_id(f"{n}>{k}")
        else:
            p = h.get_qubit_by_id(f"{n}<{k}")
        print(f"{p.measure()}", end='')


def check_correlations(hosts: list[Host], logical_qubits: int,
                       code_length: int = 3):
    print("Checking correlations")
    print("Alice: ", end='')
    for n in range(logical_qubits):
        pretty_print_logical_qubit(hosts[0], n, code_length)
    print()
    print("Bob:   ", end='')
    for n in range(logical_qubits):
        pretty_print_logical_qubit(hosts[-1], n, code_length, left_side=False)
    print()


@dataclass(init=False)
class LinearRepeaterNetwork:
    """
    LinearRepeaternetwork creates a linear topology where boundary nodes, Alice
    and Bob, are separated by repeaters-many repeater nodes.

    The method `run_with_repetition_code` will establish an encoded Φ^+ between
    Alice and Bob in three steps.

    1. Encoded generation. An encoded Φ^+ is established between neighbours in
    three steps:

    1.1. memory qubits are prepared in encoded states |+> and |0> at
         neighbouring stations.
    1.2. a physical Bell pair is generated and shared for each physical qubit
         in the code block
    1.3. the prepared memory qubits are teleported through remote CNOT gates to
         create an encoded |00> + |11>

    2. Encoded Connection. A transverse Bell basis measurement is performed at
    each repeater node. The measurement result is sent to the appropriate
    neighbours.

    3. Pauli Frame Correction. A local gate is applied transversely to account
    for the measurement outcome and create an encoded Φ+ between non-
    neighbouring peers.
    """
    network: Network
    hosts: list[Host]

    def __init__(self, repeaters, delay=0.1, x_error_rate=0.3):
        self.network = Network.get_instance()
        peers = ["Alice"] + [f"Polly_{k}" for k in range(repeaters)] + ["Bob"]
        self.network.delay = delay
        self.network.x_error_rate = x_error_rate

        hosts = list(map(lambda x: Host(x), peers))
        self.hosts = hosts

        for k in range(len(peers)-1):
            hosts[k].add_connection(hosts[k+1].host_id)
            hosts[k+1].add_connection(hosts[k].host_id)

        for host in hosts:
            self.network.add_host(host)
            host.start()

        self.network.start(nodes=peers)

    def __len__(self):
        return len(self.hosts)

    def __getitem__(self, i):
        return self.hosts[i]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.network.stop()

    @property
    def num_repeaters(self):
        return len(self.hosts) - 2

    def run_with_repetition_code(self, logical_qubits: int = 3,
                                 code_length: int = 3):
        print(f"Establishing {logical_qubits} logical Φ^+"
              f" with code length {code_length}"
              f" using {self.num_repeaters} intermediate repeater nodes")

        egs = [EncodedGenerationProtocol(self[i], self[i+1],
                                         code_length=code_length)
               for i in range(len(self)-1)]

        # Repeat the protocol to assemble encoded entangled qubits.
        for n in range(logical_qubits):
            # 1. Encoded Generation. Generate one logical Φ^+ between
            # neighbours.
            ts = []
            for eg in egs:
                ts.append(eg.left.run_protocol(eg.left_protocol, (n,)))
                ts.append(eg.right.run_protocol(eg.right_protocol, (n,)))
            for t in ts:
                t.join()

            # Perform the swap synchronously from the left-most repeater. This
            # creates a sequence like:
            #    Alice <=> Polly_0 <=> Polly_1 <=> Bob
            #    Alice <=============> Polly_1 <=> Bob
            #    Alice <=========================> Bob
            for k in range(self.num_repeaters):
                a, p, b = self[0], self[k+1], self[k+2]

                # 2. Encoded Connection
                t1 = p.run_protocol(encoded_connection, (a, b, n, code_length))

                # 3. Establish Pauli Frame
                t2 = a.run_protocol(pauli_frame_left, (p, n, code_length))
                t3 = b.run_protocol(pauli_frame_right, (p, n, code_length))

                t1.join()
                t2.join()
                t3.join()


def main():
    logical_qubits = 5
    code_length = 3
    repeater_nodes = 2

    with LinearRepeaterNetwork(repeater_nodes) as network:
        network.run_with_repetition_code(logical_qubits=logical_qubits,
                                         code_length=code_length)
        check_correlations(network.hosts, logical_qubits, code_length)


if __name__ == "__main__":
    main()
