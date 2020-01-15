############
Introduction
############

QuNetSim (Quantum Network Simulator) is a Python based simulation framework for quantum networks. The intended use is
that one can develop and test applications and protocols designed for networks *on the network and application layer* that have the ability to transmit
and store quantum information. QuNetSim offers a framework for developing such protocols over multi-hop quantum networks
that require potentially complicated routes.

One of QuNetSim's core features is that it comes with common networking tasks already developed. Some examples of such tasks
are teleporting qubits, distributing entanglement, sending superdense coded messages, and generating secret keys with quantum
key distribution. The full list of applications built into QuNetSim can be found in the **[TODO: fill in]** section. QuNetSim
uses entanglement swapping to generate entanglement between distant (i.e. multi-step connections) hosts.

Another feature is that we allow for routing to be customized. QuNetSim uses graph objects, specifically the Python
library `networkx <https://networkx.github.io/>`__, to generate its network structures (i.e. one for classical and one for quantum).In QuNetSim, one
can establish in a sense, two networks, one for classical connections and one for quantum connections. This allows the
user to test their own routing algorithms with lots of flexibility, based on both the classical and quantum network state.
We provide a simple example of routing based on the amount of entanglement already generated in the Examples section **[TODO: fill in]**.

QuNetSim is not an event-driven simulation, meaning that events are happening asynchronously at arbitrary times,
and it is sometimes up to the user to develop robust protocols to avoid out of order arrivals at the hosts.
We provide some features to help with this, for example, packets come with a sequence number and also one can choose to
block a thread until an acknowledgement is returned.

QuNetSim is still a work in progress and in its current state, it is more of a toy example to demonstrate and create
quantum networking protocols at a high level that could potentially make their way into real applications for quantum networks.
QuNetSim, presently, is not designed to accurately simulate quantum physics and therefore quantum memories and quantum states are
generally not noisy. One has some flexibility in this regard, but it is, at the moment, very limited.

The intended user of QuNetSim is mainly those who want to learn more about quantum networks but are relatively new to
it, and generally students and instructors could use it to demonstrate some quantum networking protocols.
The goal of QuNetSim, as the name suggests, is to simulate a quantum-enabled network. To this end, we aim to allow for the writing and testing of robust protocols for multi-hop quantum information transmission with various network parameters, such as packet and qubit loss and random qubit errors. We allow a developer to develop protocols for network topologies where the types of connections between the nodes are classical, quantum, or both classically and quantumly and we provide built in quantum network protocols for commonly used tasks like teleportation and entanglement distribution.QuNetSim aims to contain most of the typical features one would assume of a quantum network such that those who are new to the field of quantum communication can more easily experiment with quantum protocols.
