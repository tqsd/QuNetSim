###############
Network Objects
###############

Network Objects in QuNetSim represent the objects that are used by the network components. The use of the word "objects" is quite general, but as further iterations of QuNetSim are made, we plan to categorize these better.

Below we see the current list of network objects. Not all of the network components use all of the network objects,
for example, the *Network* component does not have a quantum storage, where hosts do. Hosts never access packets directly, but the key piece of the protocol component is to create and manipulate packets. As QuNetSim develops, we hope to use various models to better model the physics in the simulation. In the Backends
section of the Design Overview, we detail how we have structured QuNetSim so that we can replace the underlying
network components and qubit objects. We also plan to integrate the ability to add models for the quantum storage object so that it can better simulate decoherence of the stored qubits.

.. toctree::
   :maxdepth: 2
   :glob:

   objects/*

