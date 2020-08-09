from qunetsim.objects.connections.channel_models.classical_model import ClassicalModel


# TODO: Extend connection object
class ClassicalConnection(object):
    """
    An object that stores classical connection details
    """

    def __init__(self, receiver_id):
        self._receiver_id = receiver_id
        self._model = ClassicalModel()

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
