from queue import Queue
from components import protocols
from components.logger import Logger
from objects.daemon_thread import DaemonThread
from objects.qubit import Qubit
from objects.quantum_storage import QuantumStorage
from objects.classical_storage import ClassicalStorage
from objects.message import Message
from backends.cqc_backend import CQCBackend
import uuid
import time


class Host:
    """ Host object acting as either a router node or an application host node. """

    WAIT_TIME = 10

    def __init__(self, host_id, backend=None):
        """
        Return the most important thing about a person.

        Args:
            host_id: The ID of the host
            backend: The backend to use for this host

        """
        self._host_id = host_id
        self._packet_queue = Queue()
        self._stop_thread = False
        self._queue_processor_thread = None
        self._data_qubit_store = QuantumStorage()
        self._EPR_store = QuantumStorage()
        self._classical_messages = ClassicalStorage()
        self._classical_connections = []
        self._quantum_connections = []
        if backend is None:
            self._backend = CQCBackend()
        else:
            self._backend = backend
        # add this host to the backend

        self._backend.add_host(self)
        self._max_ack_wait = None
        # Frequency of queue processing
        self._delay = 0.1
        self.logger = Logger.get_instance()
        # Packet sequence numbers per connection
        self._max_window = 10
        # [Queue, sender, seq_num, timeout, start_time]
        self._ack_receiver_queue = []
        # sender: host -> int
        self._seq_number_sender = {}
        # sender_ack: host->[received_list, low_number]
        self._seq_number_sender_ack = {}
        # receiver: host->[received_list, low_number]
        self._seq_number_receiver = {}
        self.qkd_keys = {}

    @property
    def host_id(self):
        """
        Get the *host_id* of the host.

        Returns:
            (string): The host ID of the host.
        """
        return self._host_id

    @property
    def backend(self):
        return self._backend

    @property
    def classical_connections(self):
        """
        Gets the classical connections of the host.

        Returns:
            classical connections
        """
        return self._classical_connections

    def get_connections(self):
        """
        Get a list of the connections with the types.

        Returns:

        """
        connection_list = []
        for c in self._classical_connections:
            connection_list.append({'type': 'classical', 'connection': c})
        for q in self._quantum_connections:
            connection_list.append({'type': 'quantum', 'connection': q})
        return connection_list

    @property
    def classical(self):
        """
        Gets the received classical messages sorted with the sequence number.

        Returns:
             Array: Sorted array of classical messages.
        """
        return sorted(self._classical_messages.get_all(), key=lambda x: x.seq_num, reverse=True)

    @property
    def EPR_store(self):
        return self._EPR_store

    @property
    def data_qubit_store(self):
        return self._data_qubit_store

    @property
    def delay(self):
        """
        Get the delay of the queue processor.

        Returns:
            The delay per tick for the queue processor.
        """
        return self._delay

    @delay.setter
    def delay(self, delay):
        """
        Set the delay of the queue processor.

        Args:
            delay (float): The delay per tick for the queue processor.

        """
        if not (isinstance(delay, int) or isinstance(delay, float)):
            raise Exception('delay should be a number')

        if delay < 0:
            raise Exception('Delay should not be negative')

        self._delay = delay

    @property
    def max_ack_wait(self):
        """
        Get the maximum amount of time to wait for an ACK

        Returns:
            (float): The maximum amount of time to wait for an ACK
        """
        return self._max_ack_wait

    @max_ack_wait.setter
    def max_ack_wait(self, max_ack_wait):
        """
        Set the maximum amount of time to wait for an ACK

        Args:
            max_ack_wait (float): The maximum amount of time to wait for an ACK
        """

        if not (isinstance(max_ack_wait, int) or isinstance(max_ack_wait, float)):
            raise Exception('max ack wait should be a number')

        if max_ack_wait < 0:
            raise Exception('max ack wait should be non-negative')

        self._max_ack_wait = max_ack_wait

    @property
    def storage_epr_limit(self):
        """
        Get the maximum number of qubits that can be held in EPR memory.

        Returns:
            (int): The maximum number of qubits that can be held in EPR memory.
        """
        return self._EPR_store.storage_limit

    @storage_epr_limit.setter
    def storage_epr_limit(self, storage_limit):
        """
        Set the maximum number of qubits that can be held in EPR memory.

        Args:
            storage_limit (int): The maximum number of qubits that can be held in EPR memory
        """

        if not isinstance(storage_limit, int):
            raise Exception('memory limit should be an integer')

        self._EPR_store.set_storage_limit(storage_limit, None)

    @property
    def storage_limit(self):
        """
        Get the maximum number of qubits that can be held in data qubit memory.

        Returns:
            (int): The maximum number of qubits that can be held in data qubit memory.
        """
        return self._data_qubit_store.storage_limit

    @storage_limit.setter
    def storage_limit(self, storage_limit):
        """
        Set the maximum number of qubits that can be held in data qubit memory.

        Args:
            storage_limit (int): The maximum number of qubits that can be held in data qubit memory
        """

        if not isinstance(storage_limit, int):
            raise Exception('memory limit should be an integer')

        self._data_qubit_store.set_storage_limit(storage_limit, None)

    @property
    def quantum_connections(self):
        """
        Get the quantum connections for the host.

        Returns:
            (list): The quantum connections for the host.
        """
        return self._quantum_connections

    def _get_sequence_number(self, host):
        """
        Get and set the next sequence number of connection with a receiver.

        Args:
            host(string): The ID of the receiver

        Returns:
            (int): The next sequence number of connection with a receiver.

        """
        if host not in self._seq_number_sender:
            self._seq_number_sender[host] = 0
        else:
            self._seq_number_sender[host] += 1
        return self._seq_number_sender[host]

    def get_sequence_number(self, host):
        """
        Get and set the next sequence number of connection with a receiver.

        Args:
            host(string): The ID of the receiver

        Returns:
            (int): The next sequence number of connection with a receiver.

        """
        if host not in self.seq_number:
            return 0

        return self.seq_number[host]

    def get_message_w_seq_num(self, sender_id, seq_num, wait=-1):
        """
        Get a message from a sender with a specific sequence number.
        Args:
            sender_id (str): The ID of the sender
            seq_num (int): The sequence number
            wait (int):

        Returns:

        """

        def _wait():
            nonlocal m
            nonlocal wait
            wait_start_time = time.time()
            while time.time() - wait_start_time < wait and m is None:
                filter_messages()

        def filter_messages():
            nonlocal m
            for message in self.classical:
                if message.sender == sender_id and message.seq_num == seq_num:
                    m = message

        m = None
        if wait > 0:
            DaemonThread(_wait).join()
            return m
        else:
            filter_messages()
            return m

    def _log_ack(self, protocol, receiver, seq):
        """
        Logs acknowledgement messages.
        Args:
            protocol (string): The protocol for the ACK
            receiver (string): The sender of the ACK
            seq (int): The sequence number of the packet
        """
        self.logger.log(self.host_id + ' awaits ' + protocol + ' ACK from ' +
                        receiver + ' with sequence ' + str(seq))

    def is_idle(self):
        """
        Returns if the host has packets to process or is idle.

        Returns:
            (boolean): If the host is idle or not.
        """
        return self._packet_queue.empty()

    def _process_packet(self, packet):
        """
        Processes the received packet.

        Args:
            packet (Packet): The received packet
        """

        def check_task(q, sender, seq_num, timeout, start_time):
            if timeout is not None and time.time() - timeout > start_time:
                q.put(False)
                return True
            if sender not in self._seq_number_sender_ack.keys():
                return False
            if seq_num < self._seq_number_sender_ack[sender][1]:
                q.put(True)
                return True
            if seq_num in self._seq_number_sender_ack[sender][0]:
                q.put(True)
                return True
            return False

        sender = packet.sender
        result = protocols.process(packet)
        if result is not None:
            msg = Message(sender, result['message'], result['sequence_number'])
            self._classical_messages.add_msg_to_storage(msg)
            if msg.content != protocols.ACK:
                self.logger.log(self.host_id + ' received ' + str(result['message']) +
                                ' with sequence number ' + str(result['sequence_number']))
            else:
                # Is ack msg
                sender = msg.sender
                if sender not in self._seq_number_sender_ack.keys():
                    self._seq_number_sender_ack[sender] = [[], 0]
                seq_num = msg.seq_num
                expected_seq = self._seq_number_sender_ack[sender][1]
                if seq_num == expected_seq:
                    self._seq_number_sender_ack[sender][1] += 1
                    expected_seq = self._seq_number_sender_ack[sender][1]
                    while len(self._seq_number_sender_ack[sender][0]) > 0 \
                            and expected_seq in self._seq_number_sender_ack[sender][0]:
                        self._seq_number_sender_ack[sender][0].remove(expected_seq)
                        self._seq_number_sender_ack[sender][1] += 1
                        expected_seq += 1
                elif seq_num > expected_seq:
                    self._seq_number_sender_ack[sender][0].append(seq_num)
                else:
                    raise Exception("Should never happen!")
                for t in self._ack_receiver_queue:
                    res = check_task(*t)
                    if res is True:
                        self._ack_receiver_queue.remove(t)

    def _process_queue(self):
        """
        Runs a thread for processing the packets in the packet queue.
        """

        self.logger.log('Host ' + self.host_id + ' started processing')
        while True:
            if self._stop_thread:
                break

            time.sleep(self.delay)
            if not self._packet_queue.empty():
                packet = self._packet_queue.get()
                if not packet:
                    raise Exception('empty message')
                DaemonThread(self._process_packet, args=(packet,))

    def rec_packet(self, packet):
        """
        Puts the packet into the packet queue of the host.

        Args:
            packet: Received packet.
        """
        self._packet_queue.put(packet)

    def add_c_connection(self, receiver_id):
        """
        Adds the classical connection to host with ID *receiver_id*.

        Args:
            receiver_id (string): The ID of the host to connect with.
        """
        self.classical_connections.append(receiver_id)

    def add_q_connection(self, receiver_id):
        """
        Adds the quantum connection to host with ID *receiver_id*.

        Args:
            receiver_id (string): The ID of the host to connect with.
        """
        self.quantum_connections.append(receiver_id)

    def add_connection(self, receiver_id):
        """
        Adds the classical and quantum connection to host with ID *receiver_id*.

        Args:
            receiver_id (string): The ID of the host to connect with.

        """
        self.classical_connections.append(receiver_id)
        self.quantum_connections.append(receiver_id)

    def send_ack(self, receiver, seq_number):
        """
        Sends the classical message to the receiver host with
        ID:receiver

        Args:
            receiver (string): The ID of the host to send the message.
            seq_number (int): Sequence number of the acknowleged packet.

        """
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver,
                                  protocol=protocols.SEND_CLASSICAL,
                                  payload=protocols.ACK,
                                  payload_type=protocols.SIGNAL,
                                  sequence_num=seq_number,
                                  await_ack=False)
        if receiver not in self._seq_number_receiver:
            self._seq_number_receiver[receiver] = [[], 0]
        expected_seq = self._seq_number_receiver[receiver][1]
        if expected_seq + self._max_window < seq_number:
            raise Exception("Message with seq number %d did not come before the receiver window closed!" % expected_seq)
        elif expected_seq < seq_number:
            self._seq_number_receiver[receiver][0].append(seq_number)
        else:
            self._seq_number_receiver[receiver][1] += 1
            expected_seq = self._seq_number_receiver[receiver][1]
            while len(self._seq_number_receiver[receiver][0]) > 0 and expected_seq in \
                    self._seq_number_receiver[receiver][0]:
                self._seq_number_receiver[receiver][0].remove(expected_seq)
                self._seq_number_receiver[receiver][1] += 1
                expected_seq += 1
        self._packet_queue.put(packet)

    def await_ack(self, sequence_number, sender):
        """
        Block until an ACK for packet with sequence number arrives.
        Args:
            sequence_number: The sequence number to wait for.
            sender: The sender of the ACK
        Returns:
            The status of the ACK
        """

        def wait():
            nonlocal did_ack
            start_time = time.time()
            q = Queue()
            task = (q, sender, sequence_number, self.max_ack_wait, start_time)
            self._ack_receiver_queue.append(task)
            res = q.get()
            did_ack = res
            return

        did_ack = False
        wait()
        return did_ack

    def send_classical(self, receiver_id, message, await_ack=False):
        """
        Sends the classical message to the receiver host with
        ID:receiver

        Args:
            receiver_id (string): The ID of the host to send the message.
            message (string): The classical message to send.
            await_ack (bool): If sender should wait for an ACK.
        Returns:
            boolean: If await_ack=True, return the status of the ACK
        """
        seq_num = self._get_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_CLASSICAL,
                                  payload=message,
                                  payload_type=protocols.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends CLASSICAL to " + receiver_id + " with sequence " + str(seq_num))
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('classical', receiver_id, seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_epr(self, receiver_id, q_id=None, await_ack=False, block=False):
        """
        Establish an EPR pair with the receiver and return the qubit
        ID of pair.

        Args:
            receiver_id (string): The receiver ID
            q_id (string): The ID of the qubit
            await_ack (bool): If sender should wait for an ACK.
            block (bool): If the created EPR pair should be blocked or not.
        Returns:
            string, boolean: If await_ack=True, return the ID of the EPR pair and the status of the ACK
        """
        if q_id is None:
            q_id = str(uuid.uuid4())

        seq_num = self._get_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_EPR,
                                  payload={'q_id': q_id, 'blocked': block},
                                  payload_type=protocols.SIGNAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends EPR to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('EPR', receiver_id, seq_num)
            return q_id, self.await_ack(seq_num, receiver_id)

        return q_id

    def send_teleport(self, receiver_id, q, await_ack=False, payload=None, generate_epr_if_none=True):
        """
        Teleports the qubit *q* with the receiver with host ID *receiver*

        Args:
            receiver_id (string): The ID of the host to establish the EPR pair with
            q (Qubit): The qubit to teleport
            await_ack (bool): If sender should wait for an ACK.
            payload:
            generate_epr_if_none: Generate an EPR pair with receiver if one doesn't exist
        Returns:
            boolean: If await_ack=True, return the status of the ACK
        """
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_TELEPORT,
                                  payload={'q': q, 'generate_epr_if_none': generate_epr_if_none},
                                  payload_type=protocols.CLASSICAL,
                                  sequence_num=self._get_sequence_number(receiver_id),
                                  await_ack=await_ack)
        if payload is not None:
            packet.payload = payload

        self.logger.log(self.host_id + " sends TELEPORT to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('TELEPORT', receiver_id, packet.seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_superdense(self, receiver_id, message, await_ack=False):
        """
        Send the two bit binary (i.e. '00', '01', '10', '11) message via superdense
        coding to the receiver with receiver ID *receiver_id*.

        Args:
            receiver_id (string): The receiver ID to send the message to
            message (string): The two bit binary message
            await_ack (bool): If sender should wait for an ACK.
        Returns:
           boolean: If await_ack=True, return the status of the ACK
        """
        if message not in ['00', '01', '10', '11']:
            raise ValueError("Can only sent one of '00', '01', '10', or '11' as a superdense message")

        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_SUPERDENSE,
                                  payload=message,
                                  payload_type=protocols.CLASSICAL,
                                  sequence_num=self._get_sequence_number(receiver_id),
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends SUPERDENSE to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('SUPERDENSE', receiver_id, packet.seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_qubit(self, receiver_id, q, await_ack=False):
        """
        Send the qubit *q* to the receiver with ID *receiver_id*.
        Args:
            receiver_id (string): The receiver ID to send the message to
            q (Qubit): The qubit to send
            await_ack (bool): If sender should wait for an ACK.
        Returns:
            string, boolean: If await_ack=True, return the ID of the qubit and the status of the ACK
        """
        q.set_blocked_state(True)
        q_id = q.id
        seq_num = self._get_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_QUBIT,
                                  payload=q,
                                  payload_type=protocols.QUANTUM,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)

        self.logger.log(self.host_id + " sends QUBIT to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('SEND QUBIT', receiver_id, packet.seq_num)
            return q_id, self.await_ack(packet.seq_num, receiver_id)
        return q_id

    def shares_epr(self, receiver_id):
        """
        Returns boolean value dependent on if the host shares an EPR pair
        with receiver with ID *receiver_id*

        Args:
            receiver_id (string): The receiver ID to check.

        Returns:
             boolean: Whether the host shares an EPR pair with receiver with ID *receiver_id*
        """
        return self._EPR_store.check_qubit_from_host_exists(receiver_id)

    def receive_epr(self, receiver_id):
        pass

    def change_epr_qubit_id(self, host_id, new_id, old_id=None):
        """
        Change an EPR pair ID to another. If *old_id* is set, then change that specific
        EPR half, otherwise change the first unblocked EPR half to the *new_id*.
        Args:
            host_id (string): The partner ID of the EPR pair.
            new_id (string): The new ID to change the qubit too
            old_id (string):  The old ID of the qubit

        Returns:
            Old if of the qubit which has been changed.
        """
        return self._EPR_store.change_qubit_id(host_id, new_id, old_id)

    def get_epr_pairs(self, host_id):
        """
        Return the dictionary of EPR pairs stored, just for the information regarding which qubits are stored.
        Does not remove the qubits from storage like *get_epr_pair* does.

        Args:
            host_id (str): Get the EPR pairs established with host with *host_id*

        Returns:
            dict: If *host_id* is not set, then return the entire dictionary of EPR pairs.
                  Else If *host_id* is set, then return the EPRs for that particular host if there are any.
                  Return an empty list otherwise.
        """
        if host_id is None:
            raise ValueError("Host id has to be specified!")
        return self._EPR_store.get_all_qubits_from_host(host_id)

    def get_data_qubits(self, host_id):
        """
        Return the dictionary of data qubits stored, just for the information regarding which qubits are stored.
        Does not remove the qubits from storage like *get_data_qubit* does.

        Args:
            host_id (int): The host id from which the data qubit have been received.

        Returns:
            dict: If *host_id* is not set, then return the entire dictionary of data qubits.
                  Else If *host_id* is set, then return the data qubits for that particular host if there are any.
                  Return an empty list otherwise.
        """
        return self._data_qubit_store.get_all_qubits_from_host(host_id)

    def set_epr_memory_limit(self, limit, host_id=None):
        """
        Set the limit to how many EPR pair halves can be stored from host_id, or if host_id is not set,
        use the limit for all connections.

        Args:
            limit (int): The maximum number of qubits for the memory
            host_id (str): (optional) The partner ID to set the limit with
        """
        self._EPR_store.set_storage_limit(limit, host_id)

    def set_data_qubit_memory_limit(self, limit, host_id=None):
        """
        Set the limit to how many data qubits can be stored from host_id, or if host_id is not set,
        use the limit for all connections.

        Args:
            limit (int): The maximum number of qubits for the memory
            host_id (str): (optional) The partner ID to set the limit with
        """
        self._data_qubit_store.set_storage_limit(limit, host_id)

    def add_epr(self, host_id, qubit, q_id=None, blocked=False):
        """
        Adds the EPR to the EPR store of a host. If the EPR has an ID, adds the EPR with it,
        otherwise generates an ID for the EPR and adds the qubit with that ID.

        Args:
            host_id (String): The ID of the host to pair the qubit
            qubit(Qubit): The data Qubit to be added.
            q_id(string): The ID of the qubit to be added.
            blocked: If the qubit should be stored as blocked or not
        Returns:
             (string) *q_id*: The qubit ID
        """
        if q_id is not None:
            qubit.set_new_id(q_id)
        qubit.set_blocked_state(blocked)
        self._EPR_store.add_qubit_from_host(qubit, host_id)
        return qubit.id

    def add_data_qubit(self, host_id, qubit, q_id=None):
        """
        Adds the data qubit to the data qubit store of a host. If the qubit has an ID, adds the qubit with it,
        otherwise generates an ID for the qubit and adds the qubit with that ID.

        Args:
            host_id: The ID of the host to pair the qubit
            qubit (Qubit): The data Qubit to be added.
            q_id (str): the ID to set the qubit ID to
        Returns:
            (string) *q_id*: The qubit ID
        """
        if q_id is not None:
            qubit.set_new_id(q_id)

        self._data_qubit_store.add_qubit_from_host(qubit, host_id)
        return qubit.id

    def add_checksum(self, qubits, size_per_qubit=2):
        """
        Generate a set of qubits that represent a quantum checksum for the set of qubits *qubits*
        Args:
            qubits: The set of qubits to encode
            size_per_qubit (int): The size of the checksum per qubit (i.e. 1 qubit encoded into *size*)

        Returns:
            list: A list of qubits that are encoded for *qubits*
        """
        i = 0
        check_qubits = []
        while i < len(qubits):
            check = Qubit(self.host_id)
            j = 0
            while j < size_per_qubit:
                qubits[i + j].cnot(check)
                j += 1

            check_qubits.append(check)
            i += size_per_qubit
        return check_qubits

    def get_classical(self, host_id, wait=-1):
        """
        Get the classical messages from partner host *host_id*.

        Args:
            host_id (string): The ID of the partner who sent the clasical messages
            wait (float): How long in seconds to wait for the messages if none are set.

        Returns:
            A list of classical messages from Host with ID *host_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        def process_messages():
            nonlocal cla
            cla = self._classical_messages.get_all_from_sender(host_id)

        def _wait():
            nonlocal cla
            nonlocal wait
            wait_start_time = time.time()
            while time.time() - wait_start_time < wait and len(cla) == 0:
                process_messages()
            return cla

        if wait > 0:
            cla = []
            DaemonThread(_wait).join()
            return sorted(cla, key=lambda x: x.seq_num, reverse=True)
        else:
            cla = []
            process_messages()
            return sorted(cla, key=lambda x: x.seq_num, reverse=True)

    def get_epr(self, host_id, q_id=None, wait=-1):
        """
        Gets the EPR that is entangled with another host in the network. If qubit ID is specified,
        EPR with that ID is returned, else, the last EPR added is returned.

        Args:
            host_id (string): The ID of the host that returned EPR is entangled to.
            q_id (string): The qubit ID of the EPR to get.
            wait (float): the amount of time to wait
        Returns:
             Qubit: Qubit shared with the host with *host_id* and *q_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        def _wait():
            nonlocal q
            nonlocal wait
            wait_start_time = time.time()
            while time.time() - wait_start_time < wait and q is None:
                q = _get_qubit(self._EPR_store, host_id, q_id)
            return q

        if wait > 0:
            q = None
            DaemonThread(_wait).join()
            return q
        else:
            return _get_qubit(self._EPR_store, host_id, q_id)

    def get_data_qubit(self, host_id, q_id=None, wait=-1):
        """
        Gets the data qubit received from another host in the network. If qubit ID is specified,
        qubit with that ID is returned, else, the last qubit received is returned.

        Args:
            host_id (string): The ID of the host that data qubit to be returned is received from.
            q_id (string): The qubit ID of the data qubit to get.
            wait (float): The amount of time to wait for the a qubit to arrive
        Returns:
             Qubit: Qubit received from the host with *host_id* and *q_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        def _wait():
            nonlocal q
            nonlocal wait
            wait_start_time = time.time()
            while time.time() - wait_start_time < wait and q is None:
                q = _get_qubit(self._data_qubit_store, host_id, q_id)
            return q

        if wait > 0:
            q = None
            DaemonThread(_wait).join()
            return q
        else:
            return _get_qubit(self._data_qubit_store, host_id, q_id)

    def stop(self, release_qubits=True):
        """
        Stops the host. If release_qubit is true, clear the quantum memories.

        Args:
            release_qubits (boolean): If release_qubit is true, clear the quantum memories.
        """
        self.logger.log('Host ' + self.host_id + " stopped")
        if release_qubits:
            self._data_qubit_store.release_storage()
            self._EPR_store.release_storage()

        self._backend.stop()
        self._stop_thread = True

    def start(self):
        """
        Starts the host.
        """
        self._queue_processor_thread = DaemonThread(target=self._process_queue)

    def run_protocol(self, protocol, arguments=(), blocking=False):
        """
        Run the protocol *protocol*.
        Args:
            protocol (function): The protocol that the host should run.
            arguments (tuple): The set of (ordered) arguments for the protocol
            blocking (bool): Wait for thread to stop before proceeding
        """
        arguments = (self,) + arguments
        if blocking:
            DaemonThread(protocol, args=arguments).join()
        else:
            DaemonThread(protocol, args=arguments)

    def get_next_classical_message(self, receive_from_id, buffer, sequence_nr):
        """

        Args:
            receive_from_id:
            buffer:
            sequence_nr:

        Returns:

        """
        buffer = buffer + self.get_classical(receive_from_id, wait=Host.WAIT_TIME)
        msg = "ACK"
        while msg == "ACK" or (msg.split(':')[0] != ("%d" % sequence_nr)):
            if len(buffer) == 0:
                buffer = buffer + self.get_classical(receive_from_id, wait=Host.WAIT_TIME)
            ele = buffer.pop(0)
            msg = ele.content
        return msg

    def send_key(self, receiver_id, key_size, await_ack=True):
        """
        Send a secret key via QKD of length *key_size* to host with ID *receiver_id*.
        Args:
            receiver_id (str):
            key_size (int):
            await_ack (bool):
        Returns:
            bool
        """

        seq_num = self._get_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=protocols.SEND_KEY,
                                  payload={'keysize': key_size},
                                  payload_type=protocols.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends KEY to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('EPR', receiver_id, seq_num)
            return self.await_ack(seq_num, receiver_id)


def _get_qubit(store, host_id, q_id):
    """
    Gets the data qubit received from another host in the network. If qubit ID is specified,
    qubit with that ID is returned, else, the last qubit received is returned.

    Args:
        store: The qubit storage to retrieve the qubit
        host_id (string): The ID of the host that data qubit to be returned is received from.
        q_id (string): The qubit ID of the data qubit to get.
    Returns:
         Qubit: Qubit received from the host with *host_id* and *q_id*.
    """
    return store.get_qubit_from_host(host_id, q_id)
