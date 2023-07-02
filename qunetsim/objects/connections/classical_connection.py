import unittest
from qunetsim.objects.connections.channel_models.classical_model import ClassicalModel
from qunetsim.objects.connections.connection import Connection
from .channel_models.channel_model import ChannelModel

class ClassicalConnection(Connection):
    """
    An object that stores classical connection details
    """

    def __init__(self, sender_id, receiver_id, model=None):
        if model is None:
            super().__init__(sender_id, receiver_id, ClassicalModel())
        else:
            if model.type != ChannelModel.CLASSICAL:
                raise Exception("Classical connection should have the model type - classical")
            super().__init__(sender_id, receiver_id, model)
