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
        return self._ttl

    @ttl.setter
    def ttl(self, ttl):
        if ttl >= 0:
            self._ttl = ttl

    @property
    def route(self):
        return self._route

    @property
    def sender(self):
        return self._sender

    @property
    def receiver(self):
        return self._receiver

    @property
    def payload(self):
        return self._payload

    @property
    def payload_type(self):
        return self._payload_type

    @property
    def protocol(self):
        return self._protocol

    def decrease_ttl(self):
        """
        Decreases TTL by 1.
        """
        if self.ttl > 0:
            self.ttl = self.ttl - 1
