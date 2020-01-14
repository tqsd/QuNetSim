from objects.packet import Packet


class RoutingPacket(object):
    """
    A network layer packet.
    """

    def __init__(self, sender, receiver, protocol, payload_type, payload,
                 ttl, route, ):
        """
        Encodes a packet into another packet, which has a ttl and route in
        addition.

        Args:
            sender(string): ID of the sender
            receiver(string): ID of the receiver
            protocol(string): ID of the protocol of which the packet should be processed.
            payload (Packet): The message that is intended to send with the packet. Type of payload depends on the protocol.
            payload_type(string): Type of the payload.
            ttl(int): Time-to-Live parameter
            route (List): Route the packet takes to its target host.
        """
        if not isinstance(payload, Packet):
            raise ValueError("For the routing packet the payload has to be a packet.")

        self._ttl = ttl
        self._route = route
        self._sender = sender
        self._receiver = receiver
        self._payload = payload
        self._payload_type = payload_type
        self._protocol = protocol

    @property
    def ttl(self):
        """
        Time to live (TTL) of the packet. When this goes to 0 the packet is removed
        from the network.

        Returns:
            ttl (int): The time to live of the packet.
        """
        return self._ttl

    @ttl.setter
    def ttl(self, ttl):
        """
        Set the TTL for the packet.
        Args:
            ttl (int): An integer of a least 0 representing the number of hops the packet has left to live.

        """
        if ttl >= 0:
            self._ttl = ttl

    @property
    def route(self):
        """
        The route the packet should take.

        Returns:
            route (list): A list of host IDs which the packet will travel.
        """
        return self._route

    @property
    def sender(self):
        """
        The sender ID of the packet.

        Returns:
            sender (str): The sender ID of the packet.
        """
        return self._sender

    @property
    def receiver(self):
        """
        The receiver ID of the packet.

        Returns:
            receiver (str): The receiver ID of the packet.
        """
        return self._receiver

    @property
    def payload(self):
        """
        The payload of the packet which is a transport layer packet.

        Returns:
            payload (Packet): The payload of the network packet.
        """
        return self._payload

    @property
    def payload_type(self):
        """
        If the payload is classical of quantum (i.e. a qubit or classical data).

        Returns:
            payload_type (str): The payload type.
        """
        return self._payload_type

    @property
    def protocol(self):
        """
        The network layer protocol for this packet.

        Returns:
            protocol (str): The protocol for the packet.
        """
        return self._protocol

    def decrease_ttl(self):
        """
        Decreases TTL by 1.
        """
        if self.ttl > 0:
            self.ttl = self.ttl - 1
