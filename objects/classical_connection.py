class C_Connection:
    """
    An object that stores classical connection details
    """
    def __init__(self, receiver_id, length=0.0):
        self._receiver_id = receiver_id
        self._length = length

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def length(self):
        return self._length