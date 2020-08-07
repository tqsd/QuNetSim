class C_Connection(object):
    """
    An object that stores classical connection details
    """
    def __init__(self, receiver_id):
        self._receiver_id = receiver_id
        self._model = Classical_Model()

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

class Classical_Model(object):

    def __init__(self):
        self._length = 0
        self._transmission_p = 1.0

    @property
    def length(self):
        """
        Length of the channel in Km

        Returns:
            (float) : Length of the channel in Km
        """
        return self._length

    @length.setter
    def length(self, length):
        """
        Set the length of the channel

        Args:
            length (float) : Length of the channel in Km
        """
        if not isinstance(length, int) and not isinstance(length, float):
            raise ValueError("Length must be float or int")
        elif length < 0:
            raise ValueError("Length must be non-negative")
        else:
            self._length = length

    @property
    def transmission_p(self):
        """
        Transmission probability of the channel

        Returns:
            (float) : Probability that a qubit is transmitted
        """
        return self._transmission_p

    @transmission_p.setter
    def transmission_p(self, probability):
        """
        Set the transmission probability of the channel

        Args
            probability (float) : Probability that a classical packet is transmitted
        """
        if not isinstance(probability, int) and not isinstance(probability, float):
            raise ValueError("Transmission probability must be float or int")
        elif probability < 0 or probability > 1:
            raise ValueError("Transmission probability must lie in the interval [0, 1]")
        else:
            self._transmission_p = probability