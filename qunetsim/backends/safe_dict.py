from qunetsim.backends.rw_lock import RWLock


class SafeDict(object):
    def __init__(self):
        self.lock = RWLock()
        self.dict = {}

    def __str__(self):
        self.lock.acquire_read()
        ret = str(self.dict)
        self.lock.release_read()
        return ret

    def add_to_dict(self, key, value):
        self.lock.acquire_write()
        self.dict[key] = value
        self.lock.release_write()

    def get_from_dict(self, key):
        ret = None
        self.lock.acquire_read()
        if key in self.dict:
            ret = self.dict[key]
        self.lock.release_read()
        return ret
