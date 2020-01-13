from objects.qubit import Qubit
from components import protocols

# DATA KINDS
SIGNAL = 'signal'
CLASSICAL = 'classical'
QUANTUM = 'quantum'
ACK = 'ACK'
NACK = 'NACK'


class Packet(object):
    """
    A transport layer packet.
    """

    def __init__(self, sender, receiver, protocol, payload_type, payload,
                 sequence_number=-1, await_ack=False):
        """
        Encodes the data with the sender, receiver, protocol, payload type and sequence number and forms the packet
        with data and the header.

        Args:
            sender(string): ID of the sender
            receiver(string): ID of the receiver
            protocol(string): ID of the protocol of which the packet should be processed.
            payload (Object): The message that is intended to send with the packet. Type of payload depends on the protocol.
            payload_type(string): Type of the payload.
            sequence_number (int): Sequence number of the packet.
            await_ack(bool): If the sender should await an ACK
        """
        if payload_type == QUANTUM:
            if not isinstance(payload, Qubit):
                raise ValueError("For a quantum payload, the payload has to be a qubit!")

        if protocol == protocols.RELAY:
            raise ValueError("Use a Routing packet for the relay protocol.")

        self._sender = sender
        self._receiver = receiver
        self._protocol = protocol
        self._payload_type = payload_type
        self._payload = payload
        self._seq_num = sequence_number
        self._await_ack = await_ack

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, sender):
        self._sender = sender

    @property
    def receiver(self):
        return self._receiver

    @receiver.setter
    def receiver(self, receiver):
        self._receiver = receiver

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, protocol):
        self._protocol = protocol

    @property
    def payload_type(self):
        return self._payload_type

    @payload_type.setter
    def payload_type(self, payload_type):
        self._payload_type = payload_type

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload

    @property
    def seq_num(self):
        return self._seq_num

    @seq_num.setter
    def seq_num(self, seq_num):
        self._seq_num = seq_num

    @property
    def await_ack(self):
        return self._await_ack

    @await_ack.setter
    def await_ack(self, await_ack):
        self._await_ack = await_ack
