from qunetsim.objects.connections.channel_models.fibre import Fibre


# TODO: Extend connection object
class QuantumConnection(object):
    """
    An object that stores quantum connection details
    """

    def __init__(self, receiver_id, model=None):
        self._receiver_id = receiver_id
        if model is None:
            self._model = Fibre()  # Defaults to fibre model
        else:
            self._model = model

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
