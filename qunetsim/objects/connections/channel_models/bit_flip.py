import random
from qunetsim.objects.connections.channel_models.channel_model import ChannelModel

class BitFlip(ChannelModel):
    """
    The model for a bit flip quantum connection.
    """

    def __init__(self, probability=0.0):
        super().__init__(ChannelModel.QUANTUM)
        if not isinstance(probability, int) and not isinstance(probability, float):
            raise ValueError("Bit Flip probability must be float or int")
        elif probability < 0 or probability > 1:
            raise ValueError("Bit Flip probability must lie in the interval [0, 1]")
        else:
            self._p = probability

    @property
    def bitflip_probability(self):
        """
        Probability of bit flip of qubit

        Returns
            (float) : Probability that a qubit is flipped during transmission
        """
        return self._p

    @bitflip_probability.setter
    def bitflip_probability(self, probability):
        """
        Set the bit flip probability of the channel

        Args
            probability (float) : Probability that a qubit is flipped during transmission
        """
        if not isinstance(probability, int) and not isinstance(probability, float):
            raise ValueError("Bit flip probability must be float or int")
        elif probability < 0 or probability > 1:
            raise ValueError("Bit flip probability must lie in the interval [0, 1]")
        else:
            self._p = probability

    def qubit_func(self, qubit):
        """
        Function to modify the qubit based on channel properties
        In this case - Returns flipped qubit, otherwise returns the original qubit
        Required in all channel models

        Returns
            (object) : Modified qubit
        """
        if random.random() > (1.0 - self.bitflip_probability):
            if qubit is not None:
                qubit.X()
            return qubit
        else:
            return qubit
        