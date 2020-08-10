from qunetsim.objects.connections.channel_models.classical_model import ClassicalModel
from qunetsim.objects.connections.connection import Connection

class ClassicalConnection(Connection):
    """
    An object that stores classical connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        if model is None:
            self._model = ClassicalModel()
        else:
            self._model = model
