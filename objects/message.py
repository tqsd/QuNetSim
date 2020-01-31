class Message(object):
    """
    A classical message. Contains a string message and the sender address with sequence number.
    """

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
