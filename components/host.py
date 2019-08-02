from queue import Queue
import threading
from components import protocols


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class Host:
    def __init__(self, host_id, cqc, logging=True):
        """
        Init a Host
        :param host_id: a 4 bit ID string e.g. 0110
        :param cqc: the CQCConnection
        :param logging: print log messages
        """
        self.host_id = host_id
        self._message_queue = Queue()
        self._stop_thread = False
        self._data_qubit_store = {}
        self._EPR_store = {}
        self._logging = logging
        self._classical_listener_thread = None
        self._queue_processor_thread = None
        self.cqc = cqc
        self._time = 0
        self.connections = []
        self.paths = []

    def rec_packet(self, packet):
        self._message_queue.put(packet)

    def add_connection(self, connection_id):
        self.connections.append(connection_id)

    def add_path(self, path):
        self.paths.append(path)

    def send_classical(self, receiver, message):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_CLASSICAL, message, protocols.CLASSICAL)
        print('alice sends ', packet)
        self._message_queue.put(packet)

    def process_queue(self):
        if self._logging:
            print('-- Host ' + self.host_id + ' started processing')

        while True:
            if self._stop_thread:
                break

            if not self._message_queue.empty():
                message = self._message_queue.get()
                result = protocols.process(message)
                if result:
                    print('msg', result)

                # sender = str(message[0][0:8])

                # data_qubits = None
                # eprs = None
                #
                # if not self._data_qubit_store[sender] and sender != self.host_id:
                #     self._data_qubit_store[sender] = []
                #
                # if not self._EPR_store[sender] and sender != self.host_id:
                #     self._EPR_store[sender] = []
                #
                # data_qubits = self._data_qubit_store[sender]
                # eprs = self._EPR_store[sender]

    def stop(self):
        if self._logging:
            print('-- Host ' + self.host_id + " stopped")

        self._stop_thread = True

    def start(self):
        self._queue_processor_thread = DaemonThread(target=self.process_queue)
