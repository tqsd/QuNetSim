=================
Quick Start Guide
=================

.. toctree::
   :hidden:
   :maxdepth: 2


Here we give a quick start guide on how to get your first example running with QuNetSim. After completing the
install instructions and ensuring the code is working, you can being to develop your first example. To make the first
steps simple, we include a simple template generating script. To use it, enter into your console:

:code:`python QuNetSim/templater.py`

The templating script will prompt you for a file name. This will be the file name for the example Python file.
Here we just assume the file is called :code:`testing.py`, that is, "testing" was entered into the terminal.

Next, the script will prompt for the number of nodes in the network. The template generator will set up
and example file of a fully connected network (i.e. all nodes are connected) with both types of connections, namely
classical and quantum. Opening this file assuming 4 nodes were added, we should have an new file called :code:`testing.py`
with the contents:

..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from objects.qubit import Qubit
    import time

    def protocol_1(host, receiver):
        # Here we write the protocol code for a host.
        host.send_classical(receiver, 'Hello!', await_ack=True)
        print('Message was received')

    def protocol_2(host):
        # Here we write the protocol code for another host.

        # Keep checking for classical messages for 10 seconds.
        for _ in range(10):
            time.sleep(1)
            print(host.classical[0].content)

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
       host_D.run_protocol(protocol_2, ())

    if __name__ == '__main__':
       main()


