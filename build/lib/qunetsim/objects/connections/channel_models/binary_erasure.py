import random


class BinaryErasure(object):
    """
    TODO: Add docstring
    """

    def __init__(self, probability=0.0):
        if not isinstance(probability, int) and not isinstance(probability, float):
            raise ValueError("Erasure probability must be float or int")
        elif probability < 0 or probability > 1:
            raise ValueError("Erasure probability must lie in the interval [0, 1]")
        else:
            self._p = probability

    @property
    def erasure_probability(self):
        """
        Probability of erasure of qubit

        Returns
            (float) : Probability that a qubit is erased during transmission
        """
        return self._p

    @erasure_probability.setter
    def erasure_probability(self, probability):
        """
        Set the erasure probability of the channel

        Args
            probability (float) : Probability that a qubit is erased during transmission
        """
        if not isinstance(probability, int) and not isinstance(probability, float):
            raise ValueError("Erasure probability must be float or int")
        elif probability < 0 or probability > 1:
            raise ValueError("Erasure probability must lie in the interval [0, 1]")
        else:
            self._p = probability

    def qubit_func(self, qubit):
        """
        Function to modify the qubit based on channel properties
        In this case - Returns None if qubit is erased, otherwise returns the original qubit
        Required in all channel models

        Returns
            (object) : Modified qubit
        """
        if random.random() > (1.0 - self.erasure_probability):
            if qubit is not None:
                qubit.release()
            return None
        else:
            return qubit
