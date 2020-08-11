class Connection(object):
    """
    A parent class to store methods used by QuantumConnection and ClassicalConnection objects
    """

    def __init__(self, sender_id, receiver_id, model):
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._model = model

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

    @property
    def model(self):
        """
        Channel model

        Returns:
            (object) : An object containing model characteristics
        """
        return self._model

    @model.setter
    def model(self, model):
        """
        Set the channel model

        Args
            model (object) : An object containing model characteristics and parameters
        """
        self._model = model
