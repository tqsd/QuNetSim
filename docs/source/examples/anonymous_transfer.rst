GHZ Based Anonymous Entanglement
--------------------------------

In this example, we will demonstrate how to simulate an instance of GHZ-based quantum anonymous entanglement. The goal of the protocol is to hide the creation of an entangled pair between two parties. This protocol implementation demonstrates the simplicity of translating a protocol from
a high-level mathematical syntax into simulation using QuNetSim. The protocol involves establishing GHZ states amongst :math:`n` parties as well as broadcasting measurement outcomes. 

First we develop the the behaviour of the GHZ distributor, which in this example is node :math:`A`. QuNetSim provides a function for distributing GHZ states so the function distribute simply takes the distributing host as the first parameter and the list of receiving nodes as the second. One notices that the flag distribute has been set to :code:`true` in the :code:`send_ghz` method call. This tells the sending host that it should not keep part of the GHZ state, rather, it should generate a GHZ state amongst the list given and send it to the parties in the node list, keeping no part of the state for itself.

..  code-block:: python
    :linenos:

    def distribute(host, nodes):
        # distribute=True => sender doesn't keep part of the GHZ
        host.send_ghz(nodes, distribute=True)

The next type of behaviour we would like to simulate is that of a node in the group that is not attempting to establish an EPR pair. In the anonymous entanglement protocol, the behaviour of such a node is to simply receive a piece of a GHZ state, perform a Hadamard operation on the received qubit, measure it, and broadcast to the remaining participating parties the outcome of a measurement in the computational basis. Below we see how to accomplish this. In the :code:`node` function below, the first parameter is, as always, the host that is performing the protocol. The second is the ID of the node distribution the GHZ state, which in this example, is host :math:`A`. The host fetches its GHZ state where, if it is not available at the time, they will wait ten seconds for it, accomplished by setting the :code:`wait` parameter. If they have not received part of the GHZ state, then the protocol has failed, otherwise they simply perform the Hadamard operation on the received qubit, measures it, and broadcasts the message to the network. QuNetSim includes the task of broadcasting as a built-in function and therefore the task of sending classical messages to the whole network is not only simplified, but the host performing the network does not need to know the entire network to send a broadcast.	

..  code-block:: python
    :linenos:

    def node(host, distributor):
        q = host.get_ghz(distributor, wait=10)
        if q is None:
            print('failed')
            return
        q.H()
        m = q.measure()
        host.send_broadcast(str(m))


We next implement the behaviour of the party in the protocol acting as one end of the EPR link that we label the :code:`sender`. Here we take three parameters (other than the host running the protocol), the ID of the distributor, the receiver that is the holder of the other half of the EPR pair, and an agreed upon ID for the EPR pair that will be generated. In QuNetSim, qubits have IDs for easier synchronization between parties. For EPR pairs and GHZ states, qubits share and ID, that is, the collection of qubits would all have the same ID. This is done so that when parties share many EPR pairs, they can easily synchronize their joint operations. The :code:`sender` protocol is the following: first they receive part of a GHZ state, they select a random bit and then broadcast the message so that they appear as just any other node. They then manipulate their part of their part of the GHZ state according to what the random bit was. If the bit was :math:`1`, then a :math:`Z` gate is applied. The sending party can then add the qubit as an EPR pair shared with the receiver. This EPR pair can then be used as if the sender and receiver established an EPR directly. 

..  code-block:: python
    :linenos:

    def sender(host, distributor, r, epr_id):
        q = host.get_ghz(distributor, wait=10)
        b = random.choice(['0', '1'])
        host.send_broadcast(b)
        if b == '1':
            q.Z()

        host.add_epr(r, q, q_id=epr_id)
        sending_qubit = Qubit(host)
        sending_qubit.X()
        print('Sending %s' % sending_qubit.id)
        # Generate EPR if none shouldn't change anything, but if there is
        # no shared entanglement between s and r, then there should
        # be a mistake in the protocol
        host.send_teleport(r, sending_qubit, generate_epr_if_none=False, await_ack=False)
        host.empty_classical()

Finally, we establish the behaviour of the receiver. The receiver here behaves as follows: First, in order to mask their behaviour they randomly choose a bit and broadcast it to the network. Once complete, they await the remainder of the broadcast messages. In QuNetSim, classical messages are stored as a list in the :code:`classical` field. Since there are 3 other parties, other than the receiver themself, they await the other three messages. Once they arrive, the receiver computes a global parity operation by taking the :math:`XOR` of all received bits along  with their own random choice. With this, the receiver can apply a controlled :math:`Z` gate which establishes the EPR pair with the correct sender. They simply add the EPR pair and complete the protocol.

..  code-block:: python
    :linenos:

    def receiver(host, distributor, s, epr_id):
        q = host.get_ghz(distributor, wait=10)
        b = random.choice(['0', '1'])
        host.send_broadcast(b)

        messages = []
        # Await broadcast messages from all parties
        while len(messages) < 3:
            messages = host.classical
            messages = [x for x in messages if x.content != 'ACK']
            time.sleep(0.5)

        print([m.content for m in messages])
        parity = int(b)
        for m in messages:
            if m.sender != s:
                parity = parity ^ int(m.content)

        if parity == 1:
            q.Z()

        print('established secret EPR')
        host.add_epr(s, q, q_id=epr_id)
        q = host.get_data_qubit(s, wait=10)
        host.empty_classical()
        print('Received qubit %s in the %d state' % (q.id, q.measure()))

Full example:

..  code-block:: python
    :linenos:

    import time

    from qunetsim.components.host import Host
    from qunetsim.components.network import Network
    import random

    from qunetsim.objects.qubit import Qubit


    def distribute(host, nodes):
        # distribute=True => sender doesn't keep part of the GHZ
        host.send_ghz(nodes, distribute=True)


    def sender(host, distributor, r, epr_id):
        q = host.get_ghz(distributor, wait=10)
        b = random.choice(['0', '1'])
        host.send_broadcast(b)
        if b == '1':
            q.Z()

        host.add_epr(r, q, q_id=epr_id)
        sending_qubit = Qubit(host)
        sending_qubit.X()
        print('Sending %s' % sending_qubit.id)
        # Generate EPR if none shouldn't change anything, but if there is
        # no shared entanglement between s and r, then there should
        # be a mistake in the protocol
        host.send_teleport(r, sending_qubit, generate_epr_if_none=False, await_ack=False)
        host.empty_classical()


    def receiver(host, distributor, s, epr_id):
        q = host.get_ghz(distributor, wait=10)
        b = random.choice(['0', '1'])
        host.send_broadcast(b)

        messages = []
        # Await broadcast messages from all parties
        while len(messages) < 3:
            messages = host.classical
            messages = [x for x in messages if x.content != 'ACK']
            time.sleep(0.5)

        print([m.content for m in messages])
        parity = int(b)
        for m in messages:
            if m.sender != s:
                parity = parity ^ int(m.content)

        if parity == 1:
            q.Z()

        print('established secret EPR')
        host.add_epr(s, q, q_id=epr_id)
        q = host.get_data_qubit(s, wait=10)
        host.empty_classical()
        print('Received qubit %s in the %d state' % (q.id, q.measure()))


    def node(host, distributor):
        q = host.get_ghz(distributor, wait=10)
        if q is None:
            print('failed')
            return
        q.H()
        m = q.measure()
        host.send_broadcast(str(m))


    def main():
        network = Network.get_instance()
        nodes = ['A', 'B', 'C', 'D', 'E']
        network.start(nodes)

        host_A = Host('A')
        host_A.add_connections(['B', 'C', 'D', 'E'])
        host_A.start()
        host_B = Host('B')
        host_B.add_c_connections(['C', 'D', 'E'])
        host_B.start()
        host_C = Host('C')
        host_C.add_c_connections(['B', 'D', 'E'])
        host_C.start()
        host_D = Host('D')
        host_D.add_c_connections(['B', 'C', 'E'])
        host_D.start()
        host_E = Host('E')
        host_E.add_c_connections(['B', 'C', 'D'])
        host_E.start()

        network.add_hosts([host_A, host_B, host_C, host_D, host_E])

        # Run the protocol 10 times
        for i in range(10):
            # The ID of the generated secret EPR pair has to be agreed upon in advance
            epr_id = '123'
            host_A.run_protocol(distribute, ([host_B.host_id, host_C.host_id, host_D.host_id, host_E.host_id],))
            host_B.run_protocol(node, (host_A.host_id,))
            host_C.run_protocol(node, (host_A.host_id,))
            host_D.run_protocol(sender, (host_A.host_id, host_E.host_id, epr_id))
            host_E.run_protocol(receiver, (host_A.host_id, host_D.host_id, epr_id), blocking=True)
            time.sleep(0.5)
        network.stop(True)


    if __name__ == '__main__':
        main()


