import threading


# From O'Reilly Python Cookbook by David Ascher, Alex Martelli
# with some smaller adaptions
class RWLock:
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._num_reader = 0
        self._num_writer = 0
        self._readerList = []
        self._writerList = []

    def acquire_read(self):
        self._read_ready.acquire()
        try:
            while self._num_writer > 0:
                self._read_ready.wait()
            self._num_reader += 1
        finally:
            self._readerList.append(threading.get_ident())
            self._read_ready.release()

    def release_read(self):
        self._read_ready.acquire()
        try:
            self._num_reader -= 1
            if not self._num_reader:
                self._read_ready.notifyAll()
        finally:
            self._readerList.remove(threading.get_ident())
            self._read_ready.release()

    def acquire_write(self):
        self._read_ready.acquire()
        self._num_writer += 1
        self._writerList.append(threading.get_ident())
        while self._num_reader > 0:
            self._read_ready.wait()

    def release_write(self):
        self._num_writer -= 1
        self._writerList.remove(threading.get_ident())
        self._read_ready.notifyAll()
        self._read_ready.release()
