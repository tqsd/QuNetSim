from queue import Queue, Empty
from qunetsim.components import protocols
from qunetsim.utils.constants import Constants
from qunetsim.objects import Logger, DaemonThread, Message, Packet, Qubit, QuantumStorage, ClassicalStorage
from qunetsim.backends import EQSNBackend
import uuid
import time


class Host(object):
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
        self._qubit_storage = QuantumStorage()
        self._classical_messages = ClassicalStorage()
        self._classical_connections = []
        self._quantum_connections = []
        if backend is None:
            self._backend = EQSNBackend()
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
        self._sniff_full_packet = False
        self._sniff_exclude_ACKs = True
        self._c_relay_sniffing = False
        self._c_relay_sniffing_fn = None
        self._q_relay_sniffing = False
        self._q_relay_sniffing_fn = None

    @property
    def host_id(self):
        """
        Get the *host_id* of the host.

        Returns:
            (str): The host ID of the host.
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

    @property
    def classical(self):
        """
        Gets the received classical messages sorted with the sequence number.

        Returns:
             (list): Sorted list of classical messages.
        """
        return sorted(self._classical_messages.get_all(), key=lambda x: x.seq_num, reverse=True)

    def empty_classical(self, reset_seq_nums=False):
        """
        Empty the classical message buffers.

        Args:
            reset_seq_nums (bool): if all sequence number should also be reset.
        """
        if reset_seq_nums:
            self.reset_sequence_numbers()
        self._classical_messages.empty()

    def reset_sequence_numbers(self):
        """
        Reset all sequence numbers.
        """
        self._ack_receiver_queue = []
        self._seq_number_sender = {}
        self._seq_number_sender_ack = {}
        self._seq_number_receiver = {}
        pass

    @property
    def qubit_storage(self):
        return self._qubit_storage

    @property
    def delay(self):
        """
        Get the delay of the queue processor.

        Returns:
            (float): The delay per tick for the queue processor.
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
            # Negative ack wait implies wait forever
            self._max_ack_wait = None
            return

        self._max_ack_wait = max_ack_wait

    @property
    def storage_epr_limit(self):
        """
        Get the maximum number of qubits that can be held in EPR memory.

        Returns:
            (int): The maximum number of qubits that can be held in EPR memory.
        """
        return self._qubit_storage.storage_limit

    @storage_epr_limit.setter
    def storage_epr_limit(self, storage_limit):
        """
        Set the maximum number of qubits that can be held in EPR memory.

        Args:
            storage_limit (int): The maximum number of qubits that can be held in EPR memory
        """

        if not isinstance(storage_limit, int):
            raise Exception('memory limit should be an integer')

        self._qubit_storage.storage_limit = storage_limit

    @property
    def storage_limit(self):
        """
        Get the maximum number of qubits that can be held in data qubit memory.

        Returns:
            (int): The maximum number of qubits that can be held in data qubit memory.
        """
        return self._qubit_storage.storage_limit

    @storage_limit.setter
    def storage_limit(self, storage_limit):
        """
        Set the maximum number of qubits that can be held in data qubit memory.

        Args:
            storage_limit (int): The maximum number of qubits that can be held in data qubit memory
        """

        if not isinstance(storage_limit, int):
            raise Exception('memory limit should be an integer')

        self._qubit_storage.storage_limit(storage_limit)

    @property
    def quantum_connections(self):
        """
        Get the quantum connections for the host.

        Returns:
            (list): The quantum connections for the host.
        """
        return self._quantum_connections

    @property
    def c_relay_sniffing(self):
        return self._c_relay_sniffing

    @c_relay_sniffing.setter
    def c_relay_sniffing(self, value):
        if not isinstance(value, bool):
            raise ValueError("Relay sniffing has to be a boolean.")
        self._c_relay_sniffing = value

    @property
    def c_relay_sniffing_fn(self):
        return self._c_relay_sniffing_fn

    @c_relay_sniffing_fn.setter
    def c_relay_sniffing_fn(self, func):
        """
        Set a custom function which handles messages which are routed
        through this host. Functions parameter have to be **sender, receiver,
        msg**. ACK messages are not passed to the function.

        Args:
            func (function): Function with sender, receiver, msg args.
        """
        self._c_relay_sniffing_fn = func

    def get_connections(self):
        """
        Get a list of the connections with the types.

        Returns:
            (list): The list of connections for this host.
        """
        connection_list = []
        for c in self._classical_connections:
            connection_list.append({'type': 'classical', 'connection': c})
        for q in self._quantum_connections:
            connection_list.append({'type': 'quantum', 'connection': q})
        return connection_list

    def relay_sniffing_function(self, sender, receiver, transport_packet):
        """
        The function called for packet sniffing.

        Args:
           sender (str): the sender of the packet
           receiver (str): the receiver of the packet
           transport_packet (Packet): the packet itself
        """
        if self.c_relay_sniffing_fn is not None \
                and isinstance(transport_packet, Packet) \
                and isinstance(transport_packet.payload, Message):
            if not self._sniff_exclude_ACKs or \
                    (self._sniff_exclude_ACKs and transport_packet.payload.content != Constants.ACK):
                if self._sniff_full_packet:
                    self._c_relay_sniffing_fn(sender, receiver, transport_packet)
                else:
                    self._c_relay_sniffing_fn(sender, receiver, transport_packet.payload)

    @property
    def sniff_full_packet(self):
        """
        If the eavesdropper should get the whole packet or just the
        payload.

        Returns:
            (bool): If the eavesdropper should get the whole packet or just the
                    payload.
        """
        return self._sniff_full_packet

    @sniff_full_packet.setter
    def sniff_full_packet(self, should_sniff_full_packet):
        """
        Set if the eavesdropper should get the whole packet or just the
        payload.

        Args:
            should_sniff_full_packet (bool): If the eavesdropper should get the whole packet or just the
                                            payload.
        """
        self._sniff_full_packet = should_sniff_full_packet

    @property
    def q_relay_sniffing(self):
        """
        If the host should sniff quantum packets.

        Returns:
            (bool): If the host should sniff quantum packets.
        """
        return self._q_relay_sniffing

    @q_relay_sniffing.setter
    def q_relay_sniffing(self, value):
        """
        If the host should sniff quantum packets.

        Args:
            (bool): If the host should sniff quantum packets.
        """
        if not isinstance(value, bool):
            raise ValueError("Quantum Relay sniffing has to be a boolean.")
        self._q_relay_sniffing = value

    @property
    def q_relay_sniffing_fn(self):
        """
        The function to apply to the qubits in transit.

        Returns:
            (function): The function to apply to the qubits in transit.
        """
        return self._q_relay_sniffing_fn

    @q_relay_sniffing_fn.setter
    def q_relay_sniffing_fn(self, func):
        """
        Set a custom function which handles qubits which are routes through this
        host. Functions parameter have to be **sender, receiver, qubit**.

        Args:
            func (function): Function with sender, receiver, qubit args.
        """
        self._q_relay_sniffing_fn = func

    def quantum_relay_sniffing_function(self, sender, receiver, qubit):
        """
        Calls the quantum relay sniffing function if one is set.
        """
        if self._q_relay_sniffing_fn is not None:
            self._q_relay_sniffing_fn(sender, receiver, qubit)

    def get_next_sequence_number(self, host):
        """
        Get and set the next sequence number of connection with a receiver.

        Args:
            host (str): The ID of the receiver

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
        Get the sequence number on the sending side of connection with a host *host*.

        Args:
            host (str): The ID of the sender

        Returns:
            (int): The next sequence number of connection with a receiver.
        """
        if host not in self._seq_number_sender:
            return 0

        return self._seq_number_sender[host]

    def get_sequence_number_receiver(self, host):
        """
        Get the sequence number on the receiving side of the connection with host *host*.

        Args:
            host (str): The ID of the connected host
        Returns:
            (int): The receiver sequence number.
        """
        if host not in self._seq_number_receiver:
            return 0

        return self._seq_number_receiver[host][1]

    def _get_message_w_seq_num(self, sender_id, seq_num, wait):
        """
        Get a message from a sender with a specific sequence number.
        Args:
            sender_id (str): The ID of the sender
            seq_num (int): The sequence number
            wait (int): The amount of time to wait. (-1 to wait forever)

        Returns:
            (Message): The message
        """

        def _wait():
            nonlocal m
            nonlocal wait
            nonlocal wait_forever

            if not wait_forever:
                wait_start_time = time.time()
                while time.time() - wait_start_time < wait and m is None:
                    filter_messages()
                    time.sleep(self.delay)
            else:
                while m is None:
                    filter_messages()
                    time.sleep(self.delay)

        def filter_messages():
            nonlocal m
            for message in self.classical:
                if message.sender == sender_id and message.seq_num == seq_num:
                    m = message

        m = None
        if wait > 0:
            wait_forever = False
            DaemonThread(_wait).join()
        elif wait == -1:
            wait_forever = True
            DaemonThread(_wait).join()
        else:
            filter_messages()
        return m

    def _log_ack(self, protocol, receiver, seq):
        """
        Logs acknowledgement messages.
        Args:
            protocol (str): The protocol for the ACK
            receiver (str): The sender of the ACK
            seq (int): The sequence number of the packet
        """
        self.logger.log(self.host_id + ' awaits ' + protocol + ' ACK from '
                        + receiver + ' with sequence ' + str(seq))

    def is_idle(self):
        """
        Returns if the host has packets to process or is idle.

        Returns:
            (bool): If the host is idle or not.
        """
        return self._packet_queue.empty()

    def _process_packet(self, packet):
        """
        Processes the received packet.

        Args:
            packet (Packet): The received packet
        """
        if self._c_relay_sniffing:
            # if it is a classical relay message, sniff it
            if packet.protocol == Constants.RELAY:
                # RELAY is a network layer protocol, the transport layer packet
                # is in the payload
                transport_packet = packet.payload
                if transport_packet.protocol == Constants.REC_CLASSICAL:
                    receiver = packet.receiver
                    sender = packet.sender
                    self.relay_sniffing_function(sender, receiver, transport_packet)

        result = protocols.process(packet)
        if result is not None:  # classical message if not None
            msg = result
            if msg.content != Constants.ACK:
                self._classical_messages.add_msg_to_storage(msg)
                self.logger.log(self.host_id + ' received ' + str(msg.content)
                                + ' with sequence number ' + str(msg.seq_num))
            else:
                # Is ack msg
                sender = msg.sender
                seq_num = msg.seq_num
                self._process_ack(sender, seq_num)

    def _process_ack(self, sender, seq_num):
        """
        Processes an ACK msg.

        Args:
            sender (str): The sender of the ack
            seq_num (int): The sequence number of the ack
        """

        def check_task(q, _sender, _seq_num, timeout, start_time):
            if timeout is not None and time.time() - timeout > start_time:
                q.put(False)
                return True
            if _sender not in self._seq_number_sender_ack:
                return False
            if _seq_num < self._seq_number_sender_ack[_sender][1]:
                q.put(True)
                return True
            if _seq_num in self._seq_number_sender_ack[_sender][0]:
                q.put(True)
                return True
            return False

        if sender not in self._seq_number_sender_ack:
            self._seq_number_sender_ack[sender] = [[], 0]
        expected_seq = self._seq_number_sender_ack[sender][1]
        if seq_num == expected_seq:
            self._seq_number_sender_ack[sender][1] += 1
            expected_seq = self._seq_number_sender_ack[sender][1]
            while len(self._seq_number_sender_ack[sender][0]) > 0 \
                    and expected_seq in self._seq_number_sender_ack[sender][0]:
                self._seq_number_sender_ack[sender][0].remove(
                    expected_seq)
                self._seq_number_sender_ack[sender][1] += 1
                expected_seq += 1
        elif seq_num > expected_seq:
            self._seq_number_sender_ack[sender][0].append(seq_num)

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
            receiver_id (str): The ID of the host to connect with.
        """
        self.classical_connections.append(receiver_id)

    def add_c_connections(self, receiver_ids):
        """
        Adds the classical connections to host with ID *receiver_id*.

        Args:
            receiver_ids (list): The IDs of the hosts to connect with.
        """
        for receiver_id in receiver_ids:
            self.classical_connections.append(receiver_id)

    def add_q_connection(self, receiver_id):
        """
        Adds the quantum connection to host with ID *receiver_id*.

        Args:
            receiver_id (str): The ID of the host to connect with.
        """
        self.quantum_connections.append(receiver_id)

    def add_q_connections(self, receiver_ids):
        """
        Adds the quantum connection to host with ID *receiver_id*.

        Args:
            receiver_ids (list): The IDs of the hosts to connect with.
        """
        for receiver_id in receiver_ids:
            self.quantum_connections.append(receiver_id)

    def add_connection(self, receiver_id):
        """
        Adds the classical and quantum connection to host with ID *receiver_id*.

        Args:
            receiver_id (str): The ID of the host to connect with.
        """
        self.classical_connections.append(receiver_id)
        self.quantum_connections.append(receiver_id)

    def add_connections(self, receiver_ids):
        """
        Adds the classical and quantum connections to host with ID *receiver_id*.

        Args:
            receiver_ids (list): A list of receiver IDs to connect with
        """
        for receiver_id in receiver_ids:
            self.classical_connections.append(receiver_id)
            self.quantum_connections.append(receiver_id)

    def remove_connection(self, receiver_id):
        """
        Remove a classical and quantum connection from a host.
        Args:
            receiver_id (str): The ID of the connection to remove

        Returns:
            (list): a two element list of the status of the removals.
        """
        c = self.remove_c_connection(receiver_id)
        q = self.remove_q_connection(receiver_id)
        return [c, q]

    def remove_c_connection(self, receiver_id):
        """
        Remove the classical connection with receiver with receiver ID *receiver_id*.
        Args:
            receiver_id (str): The ID of the receiving side of the classical connection

        Returns:
            (bool): Success status of the removal
        """
        c_index = self.classical_connections.index(receiver_id)
        if c_index > -1:
            del self.classical_connections[c_index]
            return True
        return False

    def remove_q_connection(self, receiver_id):
        """
        Remove the quantum connection with receiver with receiver ID *receiver_id*.
        Args:
            receiver_id (str): The ID of the receiving side of the quantum connection

        Returns:
            (bool): Success status of the removal
        """
        q_index = self.quantum_connections.index(receiver_id)
        if q_index > -1:
            del self.quantum_connections[q_index]
            return True
        return False

    def send_ack(self, receiver, seq_number):
        """
        Sends the classical message to the receiver host with
        ID:receiver

        Args:
            receiver (str): The ID of the host to send the message.
            seq_number (int): Sequence number of the acknowleged packet.
        """
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver,
                                  protocol=Constants.SEND_CLASSICAL,
                                  payload=Message(sender=self.host_id, content=Constants.ACK, seq_num=seq_number),
                                  payload_type=Constants.SIGNAL,
                                  sequence_num=seq_number,
                                  await_ack=False)
        self._packet_queue.put(packet)

        if receiver not in self._seq_number_receiver:
            self._seq_number_receiver[receiver] = [[], 0]
        expected_seq = self._seq_number_receiver[receiver][1]

        while expected_seq + self._max_window < seq_number:
            self.logger.log("%s: Msg with sequence number %d was not received within the receiving window." % (
                self.host_id, expected_seq))
            # just jump over this sequence number
            expected_seq += 1
            self._seq_number_receiver[receiver][1] += 1

        if expected_seq < seq_number:
            self._seq_number_receiver[receiver][0].append(seq_number)

        else:
            self._seq_number_receiver[receiver][1] += 1
            expected_seq = self._seq_number_receiver[receiver][1]
            while len(self._seq_number_receiver[receiver][0]) > 0 and expected_seq in \
                    self._seq_number_receiver[receiver][0]:
                self._seq_number_receiver[receiver][0].remove(expected_seq)
                self._seq_number_receiver[receiver][1] += 1
                expected_seq += 1

    def await_ack(self, sequence_number, sender):
        """
        Block until an ACK for packet with sequence number arrives.

        Args:
            sequence_number (int): The sequence number to wait for.
            sender (str): The sender of the ACK
        Returns:
            (bool): The status of the ACK
        """

        def wait():
            nonlocal did_ack
            did_ack = False
            start_time = time.time()
            q = Queue()
            task = (q, sender, sequence_number, self._max_ack_wait, start_time)
            self._ack_receiver_queue.append(task)
            try:
                did_ack = q.get(timeout=self._max_ack_wait)
            except Empty:
                did_ack = False
                # remove this ACK from waiting list
                self._process_ack(sender, sequence_number)
            return

        did_ack = False
        wait()
        return did_ack

    def await_remaining_acks(self, sender):
        """
        Awaits all remaining ACKs of one sender.

        Args:
            sender (str): sender for which to wait for all acks.
        """

        def wait_multiple_seqs(seq_num_list):
            queue_list = []
            start_time = time.time()
            for sequence_number in seq_num_list:
                q = Queue()
                task = (q, sender, sequence_number, self._max_ack_wait, start_time)
                self._ack_receiver_queue.append(task)
                queue_list.append(q)
            ret_list = []
            for q, seq_num in zip(queue_list, seq_num_list):
                if q.get() is False:
                    ret_list.append(seq_num)
                    # remove this seq_num from waiting list
                    self._process_ack(sender, seq_num)
            return ret_list

        last_send_seq = self._seq_number_sender[sender]
        lowest_waiting_seq = 0
        all_remaining_acks = list(range(lowest_waiting_seq, last_send_seq + 1))
        if sender in self._seq_number_sender_ack:
            lowest_waiting_seq = self._seq_number_sender_ack[sender][1]
            all_remaining_acks = list(range(lowest_waiting_seq, last_send_seq + 1))
            for received_ack in self._seq_number_sender_ack[sender][0]:
                all_remaining_acks.remove(received_ack)
        return wait_multiple_seqs(all_remaining_acks)

    def send_broadcast(self, message):
        """
        Send a broadcast message to all of the network.

        Args:
            message (str): The message to broadcast
        """
        seq_num = -1
        message = Message(sender=self.host_id, content=message, seq_num=seq_num)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=None,
                                  protocol=Constants.SEND_BROADCAST,
                                  payload=message,
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=False)
        self.logger.log(self.host_id + " sends BROADCAST message")
        self._packet_queue.put(packet)

    def send_classical(self, receiver_id, message, await_ack=False, no_ack=False):
        """
        Sends the classical message to the receiver host with
        ID:receiver

        Args:
            receiver_id (str): The ID of the host to send the message.
            message (str): The classical message to send.
            await_ack (bool): If sender should wait for an ACK.
            no_ack (bool): If this message should not use any ACK and sequencing.
        Returns:
            (bool) If await_ack=True, return the status of the ACK
        """
        seq_num = -1
        if no_ack:
            await_ack = False
        else:
            seq_num = self.get_next_sequence_number(receiver_id)
        message = Message(sender=self.host_id, content=message, seq_num=seq_num)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_CLASSICAL,
                                  payload=message,
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends CLASSICAL to "
                        + receiver_id + " with sequence " + str(seq_num))
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('classical', receiver_id, seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_epr(self, receiver_id, q_id=None, await_ack=False, no_ack=False, block=False):
        """
        Establish an EPR pair with the receiver and return the qubit
        ID of pair.

        Args:
            receiver_id (str): The receiver ID
            q_id (str): The ID of the qubit
            await_ack (bool): If sender should wait for an ACK.
            no_ack (bool): If this message should not use any ACK and sequencing.
            block (bool): If the created EPR pair should be blocked or not.
        Returns:
            (str, bool): If await_ack=True, return the ID of the EPR pair and the status of the ACK
        """
        if q_id is None:
            q_id = str(uuid.uuid4())

        seq_num = -1
        if no_ack:
            await_ack = False
        else:
            seq_num = self.get_next_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_EPR,
                                  payload={'q_id': q_id, 'blocked': block},
                                  payload_type=Constants.SIGNAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends EPR to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('EPR', receiver_id, seq_num)
            return q_id, self.await_ack(seq_num, receiver_id)

        return q_id

    def send_ghz(self, receiver_list, q_id=None, await_ack=False, no_ack=False, distribute=False):
        """
        Share GHZ state with all receiver ids in the list. GHZ state is generated
        locally.

        Args:
            receiver_list (list): A List of all Host IDs with which a GHZ state
                                  should be shared.
            q_id (str): The ID of the GHZ qubits
            await_ack (bool): If the sender should await an ACK from all receivers
            no_ack (bool): If this message should not use any ACK and sequencing.
            distribute (bool): If the sender should keep part of the GHZ state, or just
                               distribute one
        Returns:
            (str, bool): Qubit ID of the shared GHZ and ACK status
        """
        own_qubit = Qubit(self, q_id=q_id)
        q_id = own_qubit.id
        own_qubit.H()
        q_list = []
        for _ in range(len(receiver_list) - 1):
            new_qubit = Qubit(self, q_id=q_id)
            own_qubit.cnot(new_qubit)
            q_list.append(new_qubit)

        if distribute:
            q_list.append(own_qubit)
        else:
            new_qubit = Qubit(self, q_id=q_id)
            own_qubit.cnot(new_qubit)
            q_list.append(new_qubit)
            self.add_ghz_qubit(self.host_id, own_qubit)

        seq_num_list = []
        for receiver_id in receiver_list:
            seq_num = -1
            if no_ack:
                await_ack = False
            else:
                seq_num = self.get_next_sequence_number(receiver_id)
            seq_num_list.append(seq_num)

        packet = protocols.encode(sender=self.host_id,
                                  receiver=None,
                                  protocol=Constants.SEND_GHZ,
                                  payload={Constants.QUBITS: q_list, Constants.HOSTS: receiver_list},
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num_list,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends GHZ to " + str(receiver_list))
        self._packet_queue.put(packet)

        if packet.await_ack:
            ret = True
            for receiver_id, seq_num in zip(receiver_list, seq_num_list):
                self._log_ack('GHZ', receiver_id, seq_num)
                if self.await_ack(seq_num, receiver_id) is False:
                    ret = False
            return q_id, ret
        return q_id

    def get_ghz(self, host_id, q_id=None, wait=0):
        """
        Gets the GHZ qubit which has been created by the host with the host ID *host_id*.
        It is not necessary to know with whom the states are shared.

        Args:
            host_id (str): The ID of the host that creates the GHZ state.
            q_id (str): The qubit ID of the GHZ to get.
            wait (float): the amount of time to wait
        Returns:
             (Qubit): Qubit shared with the host with *host_id* and *q_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        return _get_qubit(self._qubit_storage, host_id, q_id, Qubit.GHZ_QUBIT, wait)

    def send_teleport(self, receiver_id, q, await_ack=False, no_ack=False, payload=None, generate_epr_if_none=True):
        """
        Teleports the qubit *q* with the receiver with host ID *receiver*

        Args:
            receiver_id (str): The ID of the host to establish the EPR pair with
            q (Qubit): The qubit to teleport
            await_ack (bool): If sender should wait for an ACK.
            no_ack (bool): If this message should not use any ACK and sequencing.
            payload:
            generate_epr_if_none: Generate an EPR pair with receiver if one doesn't exist

        Returns:
            (bool) If await_ack=True, return the status of the ACK
        """
        seq_num = -1
        if no_ack:
            # if no ACKs are send, await_ack is always false
            await_ack = False
        else:
            seq_num = self.get_next_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_TELEPORT,
                                  payload={
                                      'q': q, 'generate_epr_if_none': generate_epr_if_none},
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        if payload is not None:
            packet.payload = payload

        self.logger.log(self.host_id + " sends TELEPORT to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('TELEPORT', receiver_id, packet.seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_superdense(self, receiver_id, message, await_ack=False, no_ack=False):
        """
        Send the two bit binary (i.e. '00', '01', '10', '11) message via superdense
        coding to the receiver with receiver ID *receiver_id*.

        Args:
            receiver_id (str): The receiver ID to send the message to
            message (str): The two bit binary message
            await_ack (bool): If sender should wait for an ACK.
            no_ack (bool): If this message should not use any ACK and sequencing.
        Returns:
           (bool) If await_ack=True, return the status of the ACK
        """
        if message not in ['00', '01', '10', '11']:
            raise ValueError(
                "Can only sent one of '00', '01', '10', or '11' as a superdense message")

        seq_num = -1
        if no_ack:
            # if no ACKs are send, await_ack is always false
            await_ack = False
        else:
            seq_num = self.get_next_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_SUPERDENSE,
                                  payload=message,
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends SUPERDENSE to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('SUPERDENSE', receiver_id, packet.seq_num)
            return self.await_ack(packet.seq_num, receiver_id)

    def send_qubit(self, receiver_id, q, await_ack=False, no_ack=False):
        """
        Send the qubit *q* to the receiver with ID *receiver_id*.

        Args:
            receiver_id (str): The receiver ID to send the message to
            q (Qubit): The qubit to send
            await_ack (bool): If sender should wait for an ACK.
            no_ack (bool): If this message should not use any ACK and sequencing.
        Returns:
            (str, bool): If await_ack=True, return the ID of the qubit and the status of the ACK
        """
        q.blocked = True
        q_id = q.id
        seq_num = -1
        if no_ack:
            # if no ACKs are send, await_ack is always false
            await_ack = False
        else:
            seq_num = self.get_next_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_QUBIT,
                                  payload=q,
                                  payload_type=Constants.QUANTUM,
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
            receiver_id (str): The receiver ID to check.

        Returns:
             (bool): Whether the host shares an EPR pair with receiver with ID *receiver_id*
        """
        return self._qubit_storage.check_qubit_from_host_exists(receiver_id, Qubit.EPR_QUBIT)

    def change_epr_qubit_id(self, host_id, new_id, old_id=None):
        """
        Change an EPR pair ID to another. If *old_id* is set, then change that specific
        EPR half, otherwise change the first unblocked EPR half to the *new_id*.

        Args:
            host_id (str): The partner ID of the EPR pair.
            new_id (str): The new ID to change the qubit too
            old_id (str):  The old ID of the qubit

        Returns:
            (str): Old if of the qubit which has been changed.
        """
        return self._qubit_storage.change_qubit_id(host_id, new_id, old_id)

    def get_epr_pairs(self, host_id):
        """
        Return the dictionary of EPR pairs stored, just for the information regarding which qubits are stored.
        Does not remove the qubits from storage like *get_epr_pair* does.

        Args:
            host_id (str): Get the EPR pairs established with host with *host_id*

        Returns:
            (dict): If *host_id* is not set, then return the entire dictionary of EPR pairs.
                  Else If *host_id* is set, then return the EPRs for that particular host if there are any.
                  Return an empty list otherwise.
        """
        if host_id is None:
            raise ValueError("Host id has to be specified!")
        return self._qubit_storage.get_all_qubits_from_host(host_id, Qubit.EPR_QUBIT)

    def get_data_qubits(self, host_id):
        """
        Return the dictionary of data qubits stored, just for the information regarding which qubits are stored.
        Does not remove the qubits from storage like *get_data_qubit* does.

        Args:
            host_id (str): The host id from which the data qubit have been received.

        Returns:
            (dict): If *host_id* is not set, then return the entire dictionary of data qubits.
                  Else If *host_id* is set, then return the data qubits for that particular host if there are any.
                  Return an empty list otherwise.
        """
        return self._qubit_storage.get_all_qubits_from_host(host_id, Qubit.DATA_QUBIT)

    def set_epr_memory_limit(self, limit, host_id=None):
        """
        Set the limit to how many EPR pair halves can be stored from host_id, or if host_id is not set,
        use the limit for all connections.

        Args:
            limit (int): The maximum number of qubits for the memory
            host_id (str): (optional) The partner ID to set the limit with
        """
        if host_id is not None:
            self._qubit_storage.set_storage_limit_with_host(limit, host_id)
        else:
            self._qubit_storage.storage_limit = limit

    def set_data_qubit_memory_limit(self, limit, host_id=None):
        """
        Set the limit to how many data qubits can be stored from host_id, or if host_id is not set,
        use the limit for all connections.

        Args:
            limit (int): The maximum number of qubits for the memory
            host_id (str): (optional) The partner ID to set the limit with
        """
        if host_id is not None:
            self._qubit_storage.set_storage_limit_with_host(limit, host_id)
        else:
            self._qubit_storage.storage_limit = limit

    def add_epr(self, host_id, qubit, q_id=None, blocked=False):
        """
        Adds the EPR to the EPR store of a host. If the EPR has an ID, adds the EPR with it,
        otherwise generates an ID for the EPR and adds the qubit with that ID.

        Args:
            host_id (String): The ID of the host to pair the qubit
            qubit (Qubit): The data Qubit to be added.
            q_id (str): The ID of the qubit to be added.
            blocked (bool): If the qubit should be stored as blocked or not
        Returns:
             (str): The qubit ID
        """
        if q_id is not None:
            qubit.id = q_id
        qubit.blocked = blocked
        self._qubit_storage.add_qubit_from_host(qubit, Qubit.EPR_QUBIT, host_id)
        return qubit.id

    def add_data_qubit(self, host_id, qubit, q_id=None):
        """
        Adds the data qubit to the data qubit store of a host. If the qubit has an ID, adds the qubit with it,
        otherwise generates an ID for the qubit and adds the qubit with that ID.

        Args:
            host_id (str): The ID of the host to pair the qubit
            qubit (Qubit): The data Qubit to be added.
            q_id (str): the ID to set the qubit ID to
        Returns:
            (str): The qubit ID
        """
        if q_id is not None:
            qubit.id = q_id

        self._qubit_storage.add_qubit_from_host(qubit, Qubit.DATA_QUBIT, host_id)
        return qubit.id

    def add_ghz_qubit(self, host_id, qubit, q_id=None):
        """
        Adds the GHZ qubit to the storage of the host. The host id corresponds
        to the generator of the GHZ state.

        Args:
            host_id (str): The ID of the host to pair the qubit
            qubit (Qubit): The data Qubit to be added.
            q_id (str): the ID to set the qubit ID to
        Returns:
            (str): The qubit ID
        """
        if q_id is not None:
            qubit.id = q_id

        self._qubit_storage.add_qubit_from_host(qubit, Qubit.GHZ_QUBIT, host_id)
        return qubit.id

    def add_checksum(self, qubits, size_per_qubit=2):
        """
        Generate a set of qubits that represent a quantum checksum for the set of qubits *qubits*

        Args:
            qubits (list): The set of qubits to encode
            size_per_qubit (int): The size of the checksum per qubit (i.e. 1 qubit encoded into *size*)

        Returns:
            (list): A list of qubits that are encoded for *qubits*
        """
        i = 0
        check_qubits = []
        while i < len(qubits):
            check = Qubit(self)
            j = 0
            while j < size_per_qubit:
                qubits[i + j].cnot(check)
                j += 1

            check_qubits.append(check)
            i += size_per_qubit
        return check_qubits

    def get_classical(self, host_id, seq_num=None, wait=0):
        """
        Get the classical messages from partner host *host_id*.

        Args:
            host_id (str): The ID of the partner who sent the clasical messages
            seq_num (int): The sequence number of the message
            wait (float): How long in seconds to wait for the messages if none are set.

        Returns:
            (list): A list of classical messages from Host with ID *host_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        if seq_num is not None:
            return self._get_message_w_seq_num(host_id, seq_num, wait)

        cla = self._classical_messages.get_all_from_sender(host_id, wait)
        return sorted(cla, key=lambda x: x.seq_num, reverse=True)

    def get_next_classical(self, sender_id, wait=-1):
        """
        Gets the next classical message available from a sender.
        If wait is -1 (default), it is waited till a message arrives.

        Args:
            sender_id (str): ID of the sender from the returned message.
            wait (int): waiting time, default forever.
        Returns:
            (str): The message or None
        """
        return self._classical_messages.get_next_from_sender(sender_id, wait)

    def get_epr(self, host_id, q_id=None, wait=0):
        """
        Gets the EPR that is entangled with another host in the network. If qubit ID is specified,
        EPR with that ID is returned, else, the last EPR added is returned.

        Args:
            host_id (str): The ID of the host that returned EPR is entangled to.
            q_id (str): The qubit ID of the EPR to get.
            wait (float): the amount of time to wait
        Returns:
             (Qubit): Qubit shared with the host with *host_id* and *q_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        return _get_qubit(self._qubit_storage, host_id, q_id, Qubit.EPR_QUBIT, wait)

    def get_data_qubit(self, host_id, q_id=None, wait=0):
        """
        Gets the data qubit received from another host in the network. If qubit ID is specified,
        qubit with that ID is returned, else, the last qubit received is returned.

        Args:
            host_id (str): The ID of the host that data qubit to be returned is received from.
            q_id (str): The qubit ID of the data qubit to get.
            wait (float): The amount of time to wait for the a qubit to arrive
        Returns:
            (Qubit): Qubit received from the host with *host_id* and *q_id*.
        """
        if not isinstance(wait, float) and not isinstance(wait, int):
            raise Exception('wait parameter should be a number')

        return _get_qubit(self._qubit_storage, host_id, q_id, Qubit.DATA_QUBIT, wait)

    def stop(self, release_qubits=True):
        """
        Stops the host. If release_qubit is true, clear the quantum memories.

        Args:
            (boolean): If release_qubit is true, clear the quantum memories.
        """
        self.logger.log('Host ' + self.host_id + " stopped")
        if release_qubits:
            try:
                self._qubit_storage.release_storage()
            except ValueError:
                Logger.get_instance().error('Releasing qubits was not successful')
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

        Returns:
            (DaemonThread): The thread the protocol is running on
        """
        arguments = (self,) + arguments
        if blocking:
            DaemonThread(protocol, args=arguments).join()
        else:
            return DaemonThread(protocol, args=arguments)

    def get_next_classical_message(self, receive_from_id, buffer, sequence_nr):
        """
        *WILL BE DELETED*

        Args:
            receive_from_id:
            buffer:
            sequence_nr:

        Returns:
            (Message): The message
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
            receiver_id (str): The ID of the receiver
            key_size (int): The size of the key
            await_ack (bool): If the host should wait for an ACk
        Returns:
            (bool): Status of ACK
        """

        seq_num = self.get_next_sequence_number(receiver_id)
        packet = protocols.encode(sender=self.host_id,
                                  receiver=receiver_id,
                                  protocol=Constants.SEND_KEY,
                                  payload={'keysize': key_size},
                                  payload_type=Constants.CLASSICAL,
                                  sequence_num=seq_num,
                                  await_ack=await_ack)
        self.logger.log(self.host_id + " sends KEY to " + receiver_id)
        self._packet_queue.put(packet)

        if packet.await_ack:
            self._log_ack('EPR', receiver_id, seq_num)
            return self.await_ack(seq_num, receiver_id)


def _get_qubit(store, host_id, q_id, purpose, wait=0):
    """
    Gets the data qubit received from another host in the network. If qubit ID is specified,
    qubit with that ID is returned, else, the last qubit received is returned.

    Args:
        store: The qubit storage to retrieve the qubit
        host_id (str): The ID of the host that data qubit to be returned is received from.
        q_id (str): The qubit ID of the data qubit to get.
        purpose (str): The intended use of the qubit
    Returns:
        (Qubit): Qubit received from the host with *host_id* and *q_id*.
    """
    return store.get_qubit_from_host(host_id, q_id, purpose, wait)
