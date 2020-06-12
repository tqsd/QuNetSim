Routing Packet
==============

The *Routing Packet* object is simular to the *Packet* object with the difference that it is analogous
to a network layer packet from the Internet. The main difference in our implementation is that these
packets have a TTL (time to live) property such that they are eliminated from the network after
some number of relays or "hops" in the network.

.. automodule:: qunetsim.objects.routing_packet
   :members: