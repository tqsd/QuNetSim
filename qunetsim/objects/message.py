from qunetsim.utils.serialization import Serialization


class Message(object):
    """
    A classical message. Contains a string message and the sender address with sequence number.
    """

    @staticmethod
    def from_binary(binary_string):
        """
        Creates a Message object from a binary string.

        Args:
            binary_string(bytes): Bytestring of the message.

        Returns:
            msg (Message): Message of the bytestring.
        """
        # get binary parts from the binary string
        start = 0
        sender = binary_string[start:start+Serialization.SIZE_HOST_ID]
        start += Serialization.SIZE_HOST_ID
        seq_num = binary_string[start:start+Serialization.SIZE_SEQUENCE_NR]
        start += Serialization.SIZE_SEQUENCE_NR
        content = binary_string[start:start+Serialization.SIZE_MSG_CONTENT]
        start += Serialization.SIZE_MSG_CONTENT

        # turn binary data to QuNetSim data
        sender = Serialization.binary_to_host_id(sender)
        seq_num = Serialization.binary_to_integer(seq_num, signed=True)
        content = Serialization.binary_to_string(content)

        # create Packet object
        return Message(sender, content, seq_num)

    def __init__(self, sender, content, seq_num):
        """
        A classical message includes parameters for the sender ID, a content field
        which can be any type, and a sequence number.
        Args:
            sender (str): The sender's ID.
            content (Object): The content of the message.
            seq_num (int): The sequence number for the message.
        """
        self._sender = sender
        self._content = content
        self._seq_num = seq_num

    def __str__(self):
        return "Sender: " + self.sender + "\nContent: " + self.content + "\nSequence number: " + str(self.seq_num)

    @property
    def sender(self):
        """
        The sender ID of the message.

        Returns:
            sender (str): The sender ID of the message.
        """
        return self._sender

    @sender.setter
    def sender(self, sender):
        """
        Set the sender of the message.

        Args:
            sender (str): Sender ID.
        """
        self._sender = sender

    @property
    def content(self):
        """
        The content of the message.

        Returns:
            (str): The content of the message.
        """
        return self._content

    @content.setter
    def content(self, message):
        """
        Set the content of the message.

        Args:
            message (str): The message content to set
        """
        self._content = message

    @property
    def seq_num(self):
        """
        The sequence number of the message.

        Returns:
            seq_num (int): The sequence number of the message.
        """
        return self._seq_num

    @seq_num.setter
    def seq_num(self, seq_num):
        """
        Set the sequence number of the message.

        Args:
            seq_num (int):

        """
        self._seq_num = seq_num

    def to_binary(self):
        """
        Converts the message to a binary string.
        """
        binary_string = b''
        binary_string += Serialization.host_id_to_binary(self._sender)
        binary_string += Serialization.integer_to_binary(self._seq_num, Serialization.SIZE_SEQUENCE_NR, signed=True)
        binary_string += Serialization.string_to_binary(self._content, Serialization.SIZE_MSG_CONTENT)
        return binary_string
