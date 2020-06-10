class Q_Connection:
    """
    An object that stores quantum connection details
    """
    def __init__(self, receiver_id, length=1.0, alpha=0.0):
        self._receiver_id = receiver_id
        self._length = length
        self._alpha = alpha

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def length(self):
        return self._length

    @property
    def alpha(self):
        return self._alpha

    @property
    def transmission_p(self):
        return 10.0**(-1.0*self._alpha*self._length/10.0)