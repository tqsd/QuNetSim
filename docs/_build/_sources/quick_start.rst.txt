=================
Quick Start Guide
=================

.. toctree::
   :hidden:
   :maxdepth: 2


Here we give a quick start guide on how to get your first example running with QuNetSim. After completing the
install instructions and ensuring the code is working with the correct :code:`PYTHONPATH` configured, you can being to
develop your first example. To make the first steps simple, we include a simple template generating script.
To use it, enter into your console:

:code:`python QuNetSim/templater.py`

The templating script will prompt you for a file name. This will be the file name for the example Python file.
Here we just assume the file is called :code:`testing.py`, that is, "testing" was entered into the terminal.

Next, the script will prompt for the number of nodes in the network. The template generator will set up
and example file of a fully connected network (i.e. all nodes are connected) with both types of connections, namely
classical and quantum. Opening this file assuming 4 nodes were added, we should have an new file called :code:`testing.py`
with the contents as in the code-block below.

The function :code:`protocol_1` is a protocol that would run on a specific host. In the template, only two hosts
are running protocols, but one can write more protocols for so that all nodes are running some protocol.
A requirement of any protocol function is that the first parameter is the host object that will be running the protocol.
The remaining parameters are arbitrary, there can be many parameters if needed of any type. Function :code:`protocol_2`
follows the same principles and is ran on at receiving party host.

The :code:`main` function establishes the network and initiates all the hosts to begin listening for packets.
Finally the :code:`run_protocol` method is called. This method takes the defined protocol along with
the parameters to the protocol as a tuple. One should note, a single element tuple needs a comma, that is,
if we want to have a variable :code:`a` as a single element tuple, then we need to write :code:`(a,)`. For tuples with more than
one item, one simple writes the tuple normally.

By default, this template will generate a protocol can sends 5 qubits from the sender and received 5 qubits
at the receiver. Here we leave it to the developers to get creative with their protocols. For a full list
of commands that are built into hosts, see the Design Overview section.


..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from objects.qubit import Qubit
    from components.logger import Logger
    Logger.DISABLED = True


    def protocol_1(host, receiver):
        # Here we write the protocol code for a host.
        for i in range(5):
            q = Qubit(host)
            # Apply Hadamard gate to the qubit
            q.H()
            print('Sending qubit %d.' % (i+1))
            # Send qubit and wait for an acknowledgement
            host.send_qubit(receiver, q, await_ack=True)
            print('Qubit %d was received by %s.' % (i+1, receiver))


    def protocol_2(host, sender):
        # Here we write the protocol code for another host.
        for _ in range(5):
            # Wait for a qubit from Alice for 10 seconds.
            q = host.get_data_qubit(sender, wait=10)
            # Measure the qubit and print the result.
            print('%s received a qubit in the %d state.' % (host.host_id, q.measure()))


    def main():
       network = Network.get_instance()
       nodes = ['A', 'B', 'C', 'D']
       network.start(nodes)

       host_A = Host('A')
       host_A.add_connection('B')
       host_A.add_connection('C')
       host_A.add_connection('D')
       host_A.start()
       host_B = Host('B')
       host_B.add_connection('A')
       host_B.add_connection('C')
       host_B.add_connection('D')
       host_B.start()
       host_C = Host('C')
       host_C.add_connection('A')
       host_C.add_connection('B')
       host_C.add_connection('D')
       host_C.start()
       host_D = Host('D')
       host_D.add_connection('A')
       host_D.add_connection('B')
       host_D.add_connection('C')
       host_D.start()

       network.add_host(host_A)
       network.add_host(host_B)
       network.add_host(host_C)
       network.add_host(host_D)

       host_A.run_protocol(protocol_1, (host_D.host_id,))
       host_D.run_protocol(protocol_2, (host_A.host_id,))

    if __name__ == '__main__':
       main()
