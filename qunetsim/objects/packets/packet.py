from qunetsim.objects.qubit import Qubit
from qunetsim.objects.message import Message
from qunetsim.utils.constants import Constants
from qunetsim.utils.serialization import Serialization


class Packet(object):
    """
    A transport layer packet.
    """

    @staticmethod
    def from_binary(binary_string):
        # get binary parts from the binary string
        start = 0
        sender = binary_string[start:start+Serialization.SIZE_HOST_ID]
        start += Serialization.SIZE_HOST_ID
        receiver = binary_string[start:start+Serialization.SIZE_HOST_ID]
        start += Serialization.SIZE_HOST_ID
        seq_num = binary_string[start:start+Serialization.SIZE_SEQUENCE_NR]
        start += Serialization.SIZE_SEQUENCE_NR
        protocol = binary_string[start:start+Serialization.SIZE_PROTOCOL]
        start += Serialization.SIZE_PROTOCOL
        payload_type = binary_string[start:start+Serialization.SIZE_PAYLOAD_TYPE]
        start += Serialization.SIZE_PAYLOAD_TYPE
        options = binary_string[start:start+Serialization.SIZE_OPTIONS]
        start += Serialization.SIZE_OPTIONS
        payload = binary_string[start:]

        # turn binary data to QuNetSim data
        sender = Serialization.binary_to_host_id(sender)
        receiver = Serialization.binary_to_host_id(receiver)
        seq_num = Serialization.binary_to_integer(seq_num)
        protocol = Serialization.binary_to_integer(protocol)
        payload_type = Serialization.binary_to_payload_type(payload_type)
        await_ack = Serialization.binary_extract_option_field(options, 0)
        if payload_type is Constants.SIGNAL:
            payload = Message.from_binary(payload)
        elif payload_type is Constants.CLASSICAL:
            paylaod = Message.from_binary(payload)
        elif payload_type is Constants.QUANTUM:
            payload = Qubit.from_binary(payload)
        else:
            raise ValueError("Unknown payload type!")

        # create Packet object
        return Packet(sender, receiver, protocol, payload_type, paylaod, seq_num, await_ack)

    def __init__(self, sender, receiver, protocol, payload_type, payload,
                 sequence_number=-1, await_ack=False):
        """
        Encodes the data with the sender, receiver, protocol, payload type and sequence number and forms the packet
        with data and the header.

        Args:
            sender(str): ID of the sender
            receiver(str): ID of the receiver
            protocol(str): ID of the protocol of which the packet should be processed.
            payload (Object): The message that is intended to send with the packet. Type of payload depends on the protocol.
            payload_type(str): Type of the payload.
            sequence_number (int): Sequence number of the packet.
            await_ack(bool): If the sender should await an ACK
        """
        if payload_type == Constants.QUANTUM:
            if not isinstance(payload, Qubit):
                raise ValueError("For a quantum payload, the payload has to be a qubit!")

        if protocol == Constants.RELAY:
            raise ValueError("Use a Routing packet for the relay protocol.")

        self._sender = sender
        self._receiver = receiver
        self._protocol = protocol
        self._payload_type = payload_type
        self._payload = payload
        self._seq_num = sequence_number
        self._await_ack = await_ack

    def __str__(self):
        return 'Sender: %s\nReceiver: ' \
               '%s\nProtocol: %s\nSequence number: %d\n' \
               'Payload type: %s' % \
               (self._sender, self._receiver, self._protocol, self._seq_num, str(self._payload_type))

    @property
    def sender(self):
        """
        The sender ID of the packet.

        Returns:
            sender (str): The sender ID of the packet.
        """
        return self._sender

    @sender.setter
    def sender(self, sender):
        self._sender = sender

    @property
    def receiver(self):
        """
        The receiver ID of the packet.

        Returns:
            receiver (str): The receiver ID of the packet.
        """
        return self._receiver

    @receiver.setter
    def receiver(self, receiver):
        self._receiver = receiver

    @property
    def protocol(self):
        """
        The protocol constant.

        Returns:
            protocol (str): The protocol constant.
        """
        return self._protocol

    @protocol.setter
    def protocol(self, protocol):
        self._protocol = protocol

    @property
    def payload_type(self):
        """
        The type of payload (e.g. classical, quantum, etc.)

        Returns:
            payload_type (str): The type of payload.
        """
        return self._payload_type

    @payload_type.setter
    def payload_type(self, payload_type):
        self._payload_type = payload_type

    @property
    def payload(self):
        """
        The payload.

        Returns:
            payload (Object): The payload.
        """
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload

    @property
    def seq_num(self):
        """
        The sequence number of the packet.

        Returns:
            seq_num (int): The sequence number of the packet.
        """
        return self._seq_num

    @seq_num.setter
    def seq_num(self, seq_num):
        self._seq_num = seq_num

    @property
    def await_ack(self):
        """
        If the packet triggers an ACK request.

        Returns:
            await_ack (bool): If the packet triggers an ACK request.
        """
        return self._await_ack

    @await_ack.setter
    def await_ack(self, await_ack):
        self._await_ack = await_ack
