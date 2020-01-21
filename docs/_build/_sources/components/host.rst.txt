Host
====

The Host component is analogous to a host, or node in a classical network. Hosts in QuNetSim act either as a routing
node that can relay packets through the network, or they can act as a node that runs a specific protocol. It is up
to the protocol developer to configure how the nodes behave. In most cases, once the network is established,
users will run specific protocols on the nodes. Below we see all the functions in the Host component.

The most commonly used methods for Hosts are:

* :code:`add_connection(host_id)`
    * Add a classical and quantum connection to the host with id *host_id*
* :code:`get_classical(host_id, wait=N)`
    * Get a classical message from sender with host_id *host_id* and wait *N* seconds for it
* :code:`get_data_qubit(host_id, wait=N)`:
    * Get a data qubit from sender with host_id *host_id* and wait *N* seconds for it
* :code:`get_data_qubits(host_id)`:
    * Get all data qubits from sender with host_id *host_id*
* :code:`get_epr(host_id, q_id=q_id)`:
    * Get EPR pair with qubit ID *q_id* from sender with host_id *host_id*. If *q_id=None* then get the first free EPR pair
* :code:`get_epr_pairs(host_id)`:
    * Get all EPR pairs established with host with host_id *host_id*
* :code:`send_classical(host_id, message, await_ack=<bool>)`:
    * Send the classical message *message* to host with host_id *host_id*. Block until ACK arrives if *await_ack=True*
* :code:`send_key(host_id, key_size)`:
    * Send a secret key via QKD of length *key_size* to host with ID *receiver_id*.
* :code:`send_qubit(host_id, qubit, await_ack=<bool>)`:
    * Send qubit *qubit* to host with host_id *host_id*. Block until ACK arrives if *await_ack=True*.
* :code:`send_superdense(host_id, message, await_ack=<bool>)`:
    * Send a message (one of '00', '01', '10', or '11') as a superdense message
* :code:`send_teleport(host_id, qubit, await_ack=<bool>)`:
    * Teleport qubit *qubit* to host with host_id *host_id*.
* :code:`shares_epr(host_id)`:
    * Returns if the host shares entanglement already with host with host_id *host_id*
* :code:`run_protocol(protocol, protocol_params)`:
    * Run the function *protocol* with the parameters *protocol_params*.


.. automodule:: components.host
   :members:
