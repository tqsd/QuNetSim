from queue import Queue
import threading
from components import protocols
from components.logger import Logger
import uuid


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class Host:
    def __init__(self, host_id, cqc, role='host'):
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
        self._queue_processor_thread = None
        self.connections = []
        self.cqc = cqc
        self.logger = Logger.get_instance()
        self.role = role

    def rec_packet(self, packet):
        self._message_queue.put(packet)

    def add_connection(self, connection_id):
        self.connections.append(connection_id)

    def add_path(self, path):
        self.paths.append(path)

    def send_classical(self, receiver, message):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_CLASSICAL, message, protocols.CLASSICAL)
        self.logger.log('sent classical')
        self._message_queue.put(packet)

    def send_epr(self, receiver):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_EPR, payload_type=protocols.SIGNAL)
        self.logger.log(self.host_id + " sends EPR to " + receiver)
        self._message_queue.put(packet)

    def send_teleport(self, receiver, q):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_TELEPORT, q, protocols.SIGNAL)
        self.logger.log(self.host_id + " sends TELEPORT to " + receiver)
        self._message_queue.put(packet)

    def send_superdense(self, receiver, message):
        packet = protocols.encode(self.host_id, receiver, protocols.SEND_SUPERDENSE, message, protocols.CLASSICAL)
        self.logger.log(self.host_id + " sends SUPERDENSE to " + receiver)
        self._message_queue.put(packet)

    def shares_epr(self, receiver):
        return receiver in self._EPR_store and len(self._EPR_store[receiver]) != 0

    def process_queue(self):
        self.logger.log('-- Host ' + self.host_id + ' started processing')

        while True:
            if self._stop_thread:
                break

            if not self._message_queue.empty():
                message = self._message_queue.get()
                if not message:
                    raise Exception('empty message')

                sender = message['sender']

                if sender not in self._data_qubit_store and sender != self.host_id:
                    self._data_qubit_store[sender] = []

                if sender not in self._EPR_store and sender != self.host_id:
                    self._EPR_store[sender] = []

                result = protocols.process(message)
                if result:
                    self.logger.log(self.cqc.name + ' received ' + result)

    def add_epr(self, partner_id, qubit, q_id=None):
        if partner_id not in self._EPR_store and partner_id != self.host_id:
            self._EPR_store[partner_id] = []

        if q_id is None:
            q_id = str(uuid.uuid4())

        to_add = {'q': qubit, 'q_id': q_id, 'blocked': False}

        self._EPR_store[partner_id].append(to_add)
        self.logger.log(self.host_id + ' added EPR pair ' + q_id + ' with partner ' + partner_id)
        return q_id

    def add_data_qubit(self, partner_id, qubit, q_id=None):
        if partner_id not in self._data_qubit_store and partner_id != self.host_id:
            self._data_qubit_store[partner_id] = []

        if q_id is None:
            q_id = str(uuid.uuid4())

        to_add = {'q': qubit, 'q_id': q_id, 'blocked': False}

        self._data_qubit_store[partner_id].append(to_add)
        self.logger.log(self.host_id + ' added data qubit ' + q_id + ' from ' + partner_id)
        return q_id

    def get_epr(self, partner_id, q_id=None):
        if partner_id not in self._EPR_store:
            return None

        # If q_id is not specified, then return the last in the stack
        # else return the qubit with q_id q_id
        if q_id is None:
            if not self._EPR_store[partner_id][-1]['blocked']:
                self._EPR_store[partner_id][-1]['blocked'] = True
                return self._EPR_store[partner_id].pop()
            else:
                print('accessed blocked epr qubit')
        else:
            for qubit in self._EPR_store[partner_id]:
                if qubit['q_id'] == q_id:
                    return qubit['q']
        return None

    def get_data_qubit(self, partner_id, q_id=None):
        if partner_id not in self._data_qubit_store:
            return None

        # If q_id is not specified, then return the last in the stack
        # else return the qubit with q_id q_id
        if q_id is None:
            if not self._EPR_store[partner_id][-1]['blocked']:
                self._EPR_store[partner_id][-1]['blocked'] = True
                return self._data_qubit_store[partner_id].pop()
            else:
                print('accessed blocked data qubit')
        else:
            for qubit in self._data_qubit_store[partner_id]:
                if qubit['q_id'] == q_id:
                    return qubit['q']
        return None

    def stop(self):
        self.logger.log('Host ' + self.host_id + " stopped")
        self._stop_thread = True

    def start(self):
        self._queue_processor_thread = DaemonThread(target=self.process_queue)
