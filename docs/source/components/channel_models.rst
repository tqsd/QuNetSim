Channel Models
=======

Channels act as communication modes between the hosts in a network. Each host defines it's quantum and classical 
connections with the other hosts in the network. QuNetSim introduces various channel models to mimic the real-world 
quantum connections between the hosts.
The default channel model for quantum connections is fibre.

QuNetSim implements the following channel models for quantum connections:

* :code:`BitFlip(probability)`
    * Flips the single-qubit (Pauli X) passing through the channel with certain probability
* :code:`PhaseFlip(probability)`
    * Flips the phase of the single-qubit (Pauli Z) passing through the channel with certain probability 
* :code:`BinaryErasure(probability)`
    * Erases the single-qubit passing through the channel with certain probability
* :code:`Fibre(length, alpha)`
    * Erases the single-qubit passing through the channel with certain probability determined from the length and absorption coefficient (alpha) of the channel

.. automodule:: qunetsim.components.objects.connections.channel_models
   :members:
