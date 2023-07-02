class ChannelModel(object):
    """
    A parent class for all the channel models
    """
    QUANTUM = "Quantum"
    CLASSICAL = "Classical"
    def __init__(self, type) -> None:
        self.type = type