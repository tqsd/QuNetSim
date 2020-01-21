##########
Components
##########



..  toctree::
    :maxdepth: 2
    :glob:

    components/*

The key components are QuNetSim are the following: Host, Protocols, and  Network. Each component represents a layer in
the network. The Host component represents the application layer, the Protocols component the transport layer, and the
Network the network layer.

The Host object has two roles: to run applications and to relay packets in the network. Hosts come programmed with
a set of features that can be used to write network applications. Users of QuNetSim will interact mostly with the Host
components.

The Protocols component is our version of the transport layer in a network. Here, we perform the necessary encoding and
decoding procedures so that information can be packetized and put into the network. It is also responsible for generating
entanglement ahead of time when it is needed by certain applications. The Protocols component only has
private access, and users will never need to interact with the Protocols component directly.

The Network component is the key part of QuNetSim. It is responsible for routing and generating distant entanglement
when it is needed.
