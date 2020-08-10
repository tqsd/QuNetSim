class Connection(object):
    def __init__(self, sender_id, receiver_id):
        self._sender_if = sender_id
        self._receiver_id = receiver_id

    @property
    def sender_id(self):
        """
        Sender ID
        """
        return self._sender_id

    @property
    def receiver_id(self):
        """
        Receiver ID
        """
        return self._receiver_id