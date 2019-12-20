from objects.packet import Packet


class RoutingPacket(object):


    def __init__(self, sender, receiver, protocol, payload_type, payload,
                    ttl, route,):
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
        self.ttl = ttl
        self.route = route
        self.sender = sender
        self.receiver = receiver
        self.payload = payload
        self.payload_type = payload_type
        self.protocol = protocol
