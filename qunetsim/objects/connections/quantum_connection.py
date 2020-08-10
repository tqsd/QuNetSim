from qunetsim.objects.connections.channel_models.binary_erasure import BinaryErasure
from qunetsim.objects.connections.connection import Connection

class QuantumConnection(object):
    """
    An object that stores quantum connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        if model is None:
            self._connection = Connection(sender_id, receiver_id, BinaryErasure())       # Object that stores sender and receiver IDs, defaults to Identity channel
        else:
            self._connection = Connection(sender_id, receiver_id, model)

    @property
    def receiver_id(self):
        """
        Receiver ID
        """
        return self._connection.receiver_id

    @property
    def sender_id(self):
        """
        Sender ID
        """
        return self._connection.sender_id

    @property
    def model(self):
        """
        Channel model

        Returns:
            (object) : An object containing model characteristics
        """
        return self._connection.model

    @model.setter
    def model(self, model):
        """
        Set the channel model

        Args
            model (object) : An object containing model characteristics and parameters
        """
        self._connection.model = model
