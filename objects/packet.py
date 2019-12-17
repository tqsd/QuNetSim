from objects.qubit import Qubit
from components import protocols

# DATA KINDS
SIGNAL = 'signal'
CLASSICAL = 'classical'
QUANTUM = 'quantum'
ACK = 'ACK'
NACK = 'NACK'


class Packet(object):

    def __init__(self, sender, receiver, protocol, payload_type, payload,
                 sequence_number=-1, await_ack=False, ttl=None):
        """
        Encodes the data with the sender, receiver, protocol, payload type and sequence number and forms the packet
        with data and the header.

        Args:
            sender(string): ID of the sender
            receiver(string): ID of the receiver
            protocol(string): ID of the protocol of which the packet should be processed.
            payload : The message that is intended to send with the packet. Type of payload depends on the protocol.
            payload_type(string): Type of the payload.
            sequence_num(int): Sequence number of the packet.
            await_ack(bool): If the sender should await an ACK
        """
        if payload_type == QUANTUM:
            if not isinstance(payload, Qubit):
                raise ValueError("For a quantum payload, the paload has to be a qubit!")

        if protocol == protocols.RELAY:
            if ttl is None:
                raise ValueError("Relay needs a ttl.")
            self.ttl = ttl

        self.sender = sender
        self.receiver = receiver
        self.protocol = protocol
        self.payload_type = payload_type
        self.payload = payload
        self.seq_num = sequence_number
        self.await_ack = await_ack

    def add_route(self, route):
        self.route = route
