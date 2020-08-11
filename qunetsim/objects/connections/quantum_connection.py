from qunetsim.objects.connections.channel_models.binary_erasure import BinaryErasure
from qunetsim.objects.connections.connection import Connection


class QuantumConnection(Connection):
    """
    An object that stores quantum connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        if model is None:
            super().__init__(sender_id, receiver_id, BinaryErasure())
        else:
            super().__init__(sender_id, receiver_id, model)
