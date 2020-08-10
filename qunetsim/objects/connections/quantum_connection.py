from qunetsim.objects.connections.channel_models.binary_erasure import BinaryErasure
from qunetsim.objects.connections.connection import Connection

class QuantumConnection(Connection):
    """
    An object that stores quantum connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        if model is None:
            self._model = BinaryErasure()
        else:
            self._model = model