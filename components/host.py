from queue import Queue
import threading
from components import protocols
from cqc.pythonLib import CQCConnection


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
        self._time = 0
        self.connections = []
        self.paths = []
        self.cqc = cqc

    def rec_packet(self, packet):
        self._message_queue.put(packet)

    def add_connection(self, connection_id):
        self.connections.append(connection_id)

    def add_path(self, path):
        self.paths.append(path)

    def send_classical(self, receiver, message):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_CLASSICAL, message, protocols.CLASSICAL)
        if self._logging:
            print(self.host_id + " sends classical message to " + receiver)
        self._message_queue.put(packet)

    def send_epr(self, receiver):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_EPR)
        if self._logging:
            print(self.host_id + " sends EPR to " + receiver)
        self._message_queue.put(packet)

    def process_queue(self):
        if self._logging:
            print('-- Host ' + self.host_id + ' started processing')

        while True:
            if self._stop_thread:
                break

            if not self._message_queue.empty():
                message = self._message_queue.get()
                sender = str(message[0][0:8])

                if sender not in self._data_qubit_store and sender != self.host_id:
                    self._data_qubit_store[sender] = []

                if sender not in self._EPR_store and sender != self.host_id:
                    self._EPR_store[sender] = []

                result = protocols.process(message)
                if result:
                    print('msg', result)

    def add_epr(self, partner_id, qubit):
        if partner_id not in self._EPR_store and partner_id != self.host_id:
            self._EPR_store[partner_id] = []

        if self._logging:
            print(self.host_id + ' added EPR pair with partner ' + partner_id)

        self._EPR_store[partner_id].append(qubit)

    def get_epr(self, partner_id):
        if partner_id not in self._EPR_store:
            return False
        return self._EPR_store[partner_id].pop()

    def stop(self):
        if self._logging:
            print('-- Host ' + self.host_id + " stopped")

        self._stop_thread = True

    def start(self):
        self._queue_processor_thread = DaemonThread(target=self.process_queue)
