class Message(object):
    """
    A classical message.
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

    @property
    def sender(self):
        return self._sender

    @property
    def content(self):
        return self._content

    @property
    def seq_num(self):
        return self._seq_num
