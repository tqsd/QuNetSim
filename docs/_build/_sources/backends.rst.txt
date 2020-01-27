########
Backends
########

As quantum networking and quantum internet becomes a more popular field, we expect to see
a rise in the number of quantum network simulation tools as we see now with quantum computing simulation
software. In QuNetSim, we have prepared for this by structuring the network backend so that it is modular. With this,
one can simply import their own network and qubit backends, implement the necessary methods and it (*hopefully*) will work
right out of the box.

Currently we are working with two backends: `SimulaQron <http://www.simulaqron.org/>`__ and
`EQSN <https://github.com/tqsd/EQSN_python>`__, a simulator that has
been developed by the TQSD team.

If you do not chose a backend, the default backend will be SimulaQron. However, you can chose the backend explicitly,
by creating one of the backend objects and passing it as an argument to the Hosts and network. An example of how
to chose the EQSN backend is shown in the code snippet below.

..  code-block:: python
    :linenos:

    import numpy as np
    # import the eqsn backend
    from backends.eqsn_backend import EQSNBackend

    # create the EQSN backend object
    backend = EQSNBackend()

    # Initialize a network and define the host IDs in the network
    network = Network.get_instance()
    nodes = ['Alice', 'Bob', 'Eve']

    # Start the network with the hosts and explicitly set the backend
    network.start(nodes, backend)

    # Initialize the host Alice with the right backend
    host_alice = Host('Alice', backend)

    host_alice.add_connection('Bob')
    host_alice.start()

    # Initialize the host Bob with the right backend
    host_bob = Host('Bob', backend)

    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    # Initialize the host Eve with the right backend
    host_eve = Host('Eve', backend)
    host_eve.add_connection('Bob')
    host_eve.start()

    # Add the hosts to the network
    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

To chose a different backend, just initialize the backend variable with another backend object from
the QuNetSim backend package.


######################
Writing an own Backend
######################

Instead of using a provided backend, it is also possible to write an own backend. In this section,
we describe how the interfacing to a backend works.

The interface is described in the file **backends.backend**.
The interface to the backend is a class. There can be multiple instances of this
class at once, and it has to be thread safe. This class also has to store all information
which are necessary for the backend, if needed. To make these information thread safe, the
file **backend.RWLock** provides a read write lock and the file **backends.SafeDict** provides
a thread safe dictionary with some basic functionalities.
In the functions **start** and **stop**, the backend can be initialized if necessary and be destructed.

The **create_qubit** function creates a qubit in the backend. It then has to create an object
of type *Qubit*. The variable *qubit* of the object *Qubit* can be used to store some backend
specific information. Always, if a gate is called, this information can be accessed.

The function **send_qubit_to(qubit, from_host_id, to_host_id)** transmits a qubit from one host
to the other. Also, if the backend dose not need any knowledge of the owner of the qubit,
the backend has to change the owner of the *Qubit* object. Therefore, most backends will need
a dictionary which maps host_ids to host objects. We recommend using the **SafeDict** class for
it and calling the variable *_host*. The implementation for this function, would than look
the following:

..  code-block:: python
    :linenos:

    def send_qubit_to(self, qubit, from_host_id, to_host_id):

        # Backend specific stuff

        new_host = self._hosts.get_from_dict(to_host_id)
        qubit.set_new_host(new_host)


The functions **create_EPR** and **receive_EPR** are responsible for creating entangled
pairs. Calling create_EPR will return a single Qubit, calling receive_EPR on the other
Host will then give the second Qubit belonging to the pair.
It might seem weird, that there are two function for this task, and not a real Qubit is
sent over the network. Most backends will have to create two qubits in the **create_EPR**
function and buffer one of the qubits till the receive_EPR function is called.

All other functions which are part of the interface should be self-explanatory.
