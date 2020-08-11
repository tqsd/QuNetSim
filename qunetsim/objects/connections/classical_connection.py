from qunetsim.objects.connections.channel_models.classical_model import ClassicalModel
from qunetsim.objects.connections.connection import Connection


class ClassicalConnection(Connection):
    """
    An object that stores classical connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        if model is None:
            super().__init__(sender_id, receiver_id, ClassicalModel())
        else:
            super().__init__(sender_id, receiver_id, model)
