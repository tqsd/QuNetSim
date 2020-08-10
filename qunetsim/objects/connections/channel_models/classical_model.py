class ClassicalModel(object):
    """
    TODO: Add docstring
    """

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
            length (float) : Length of the channel in m
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
