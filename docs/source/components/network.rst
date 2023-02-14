Network
=======

The Network component plays an important role in QuNetSim. In each simulation, one must configure a
network with hosts. Each host defines its classical and quantum connections and when
the host is added to the network, the network builds on the two graph objects for each type
of connection it maintains. With these two network graphs, one can define their own routing algorithms for
each type of network (e.g. there can be different routing algorithms for quantum and classical information).
The default routing algorithm is set to the shortest path route between the two hosts.

The most commonly used methods for Network are:

* :code:`add_host(host)`
    * Add a host to the network
* :code:`remove_host(host)`
    * Remove a host from the network
* :code:`update_host(host)`
    * Updates the network graph when the connections of a host change
* :code:`get_host(host_id)`
    * Get the host object given the host_id
* :code:`get_APR()`
    * Get the information for all the hosts in the network
* :code:`(property) quantum_routing_algo(function)`
    * Property for the quantum routing algorithm. It should be a function with parameters that take a source ID and a destination ID and returns an ordered list which represents the route.
* :code:`(property) classical_routing_algo(function)`
    * Property for the classical routing algorithm. It should be a function with parameters that take a source ID and a destination ID and returns an ordered list which represents the route.
* :code:`(property) use_hop_by_hop(bool)`
    * If the network should recalculate the route at each node in the route (set to True) or just once at the beginning (set to False)
* :code:`(property) delay(float)`
    * the amount of delay the network should have. The network has the ability to throttle packet transmissions which is sometimes neccessary for different types of qubit / network backends.
* :code:`draw_classical_network`
    * Generate a depiction of the classical network 
* :code:`draw_quantum_network`
    * Generate a depiction of the quantum network (via matplotlib)


.. automodule:: qunetsim.components.network
   :members:
