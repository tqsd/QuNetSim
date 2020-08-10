import random


class Fibre(object):
    """
    TODO: Add docstring
    """

    def __init__(self, length=0.0, alpha=0.0):

        if not isinstance(length, int) and not isinstance(length, float):
            raise ValueError("Length must be float or int")
        elif length < 0:
            raise ValueError("Length must be non-negative")
        else:
            self._length = length

        if not isinstance(alpha, int) and not isinstance(alpha, float):
            raise ValueError("Alpha must be float or int")
        elif alpha < 0 or alpha > 1:
            raise ValueError("Alpha must lie in the interval [0, 1]")
        else:
            self._alpha = alpha

    @property
    def length(self):
        """
        Length of the channel in m

        Returns:
            (float) : Length of the channel in m
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
    def alpha(self):
        """
        Absorption coefficient of the channel in dB/m

        Returns:
            (float) : Absorption coefficient of the channel in dB/m
        """
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        """
        Set the absorption coefficient of the channel

        Args:
            alpha (float) : Absorption coefficient of the channel in dB/m
        """
        if not isinstance(alpha, int) and not isinstance(alpha, float):
            raise ValueError("Alpha must be float or int")
        elif alpha < 0 or alpha > 1:
            raise ValueError("Alpha must lie in the interval [0, 1]")
        else:
            self._alpha = alpha

    @property
    def transmission_p(self):
        """
        Transmission probability of the channel

        Returns:
            (float) : Probability that a qubit is transmitted
        """
        return 10.0 ** (-1.0 * self._alpha * self._length / 10.0)

    def qubit_func(self, qubit):
        """
        Function to modify the qubit based on channel properties
        In this case - Returns None if transmission fails or the original qubit if transmission succeeds
        Required in all channel models

        Returns
            (object) : Modified qubit
        """
        if random.random() > self.transmission_p:
            if qubit is not None:
                qubit.release()
            return None
        else:
            return qubit
