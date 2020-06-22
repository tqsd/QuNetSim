from qunetsim.backends.rw_lock import RWLock
from qunetsim.utils.constants import Constants
import queue


class ClassicalStorage(object):
    GET_NEXT = 1
    GET_ALL = 2

    """
    A classical storage for messages.
    """

    def __init__(self):
        self._host_to_msg_dict = {}
        self._host_to_read_index = {}

        # read write lock, for threaded access
        self._lock = RWLock()

        # for tracking pending requests
        # dictionary tracks the request made by a pending request.
        self._pending_request_dict = {}
        # Determines a unique ID for a pending request.
        self._request_id = 0
        # Amount of pending requests
        self._amount_pending_requests = 0

    def _check_all_requests(self):
        """
        Checks if any of the pending requests is now fulfilled.

        Returns:
            If a request is fulfilled, the request is handled and the function
            returns the message of this request.
        """
        for req_id, args in self._pending_request_dict.items():
            ret = None
            if args[2] == ClassicalStorage.GET_NEXT:
                ret = self._get_next_from_sender(args[1])
            elif args[2] == ClassicalStorage.GET_ALL:
                ret = self._get_all_from_sender(args[1])
            else:
                raise ValueError("Internal Error, this request does not exist!")

            if ret is not None:
                args[0].put(ret)
                self._remove_request(req_id)
                return ret

    def _add_request(self, args):
        """
        Adds a new request to the classical storage. If a new message arrives, it
        is checked if the request for the qubit is satisfied.

        Args:
            args (list): [Queue, from_host_id, type]
        """
        self._pending_request_dict[self._request_id] = args
        self._request_id += 1
        self._amount_pending_requests += 1
        return self._request_id

    def _remove_request(self, req_id):
        """
        Removes a pending request from the request dict.

        Args:
            req_id (int): The id of the request to remove.
        """
        if req_id in self._pending_request_dict:
            del self._pending_request_dict[req_id]
        self._amount_pending_requests -= 1

    def empty(self):
        """
        Empty the classical storage.
        """
        self._lock.acquire_write()
        self._host_to_msg_dict = {}
        self._host_to_read_index = {}
        self._lock.release_write()

    def _add_new_host_id(self, host_id):
        """
        Add a new host to the storage.

        Args:
            host_id (str): The host ID to store.
        """
        self._host_to_msg_dict[host_id] = []
        self._host_to_read_index[host_id] = 0

    def remove_all_ack(self, from_sender=None):
        """
        Removes all ACK messages stored. If from sender is given, only ACKs from
        this sender are removed.

        Args:
            from_sender (String): Host id of the sender, whos ACKs should be delted.
        """

        self._lock.acquire_write()

        def delete_all_ack_for_sender(sender_id):
            for c, msg in enumerate(self._host_to_msg_dict[sender_id]):
                if msg.content == Constants.ACK:
                    del self._host_to_msg_dict[sender_id][c]

        if from_sender is None:
            for sender in list(self._host_to_msg_dict):
                delete_all_ack_for_sender(sender)
        elif from_sender in self._host_to_msg_dict:
            delete_all_ack_for_sender(from_sender)
        self._lock.release_write()

    # TODO: refactor to "add_msg"
    def add_msg_to_storage(self, message):
        """
        Adds a message to the storage.
        """
        sender_id = message.sender
        self._lock.acquire_write()
        if sender_id not in list(self._host_to_msg_dict):
            self._add_new_host_id(sender_id)
        self._host_to_msg_dict[sender_id].append(message)
        self._check_all_requests()
        self._lock.release_write()

    def get_all_from_sender(self, sender_id, wait=0):
        """
        Get all stored messages from a sender. If delete option is set,
        the returned messages are removed from the storage.

        Args:
            sender_id (String): The host id of the host.
            wait (int): Default is 0. The maximum blocking time. -1 to block forever.

        Returns:
            List of messages of the sender. If there are none, an empty list is
            returned.
        """
        # Block forever if wait is -1
        if wait == -1:
            wait = None

        self._lock.acquire_write()
        msg = self._get_all_from_sender(sender_id)
        if msg is not None or wait == 0:
            self._lock.release_write()
            return msg if msg is not None else []

        q = queue.Queue()
        request = [q, sender_id, ClassicalStorage.GET_ALL]
        req_id = self._add_request(request)
        self._lock.release_write()

        try:
            msg = q.get(timeout=wait)
        except queue.Empty:
            pass

        if msg is None:
            self._lock.acquire_write()
            self._remove_request(req_id)
            self._lock.release_write()
            return []
        return msg

    def _get_all_from_sender(self, sender_id):
        if sender_id in list(self._host_to_msg_dict):
            return self._host_to_msg_dict[sender_id]
        return None

    def get_next_from_sender(self, sender_id, wait=0):
        """
        Gets the next, unread, message from the sender. If there is no message
        yet, it is waited for the waiting time till a message is arrived. If
        there is still no message, than None is returned.

        Args:
            sender_id (String): The sender id of the message to get.
            wait (int): Default is 0. The maximum blocking time. -1 to block forever.
        Returns:
            Message object, if such a message exists, or none.
        """
        # Block forever if wait is -1
        if wait == -1:
            wait = None

        self._lock.acquire_write()
        next_msg = self._get_next_from_sender(sender_id)
        if next_msg is not None or wait == 0:
            self._lock.release_write()
            return next_msg

        q = queue.Queue()
        request = [q, sender_id, ClassicalStorage.GET_NEXT]
        req_id = self._add_request(request)
        self._lock.release_write()

        try:
            next_msg = q.get(timeout=wait)
        except queue.Empty:
            pass

        if next_msg is None:
            self._lock.acquire_write()
            self._remove_request(req_id)
            self._lock.release_write()
        return next_msg

    def _get_next_from_sender(self, sender_id):
        if sender_id not in list(self._host_to_msg_dict):
            return None
        if len(self._host_to_msg_dict[sender_id]) <= self._host_to_read_index[sender_id]:
            return None
        msg = self._host_to_msg_dict[sender_id][self._host_to_read_index[sender_id]]
        self._host_to_read_index[sender_id] += 1
        return msg

    def get_all(self):
        """
        Get all Messages as a list.

        Returns:
            (list) messages: All Messages as a list.
        """
        self._lock.acquire_write()
        ret = []
        for host_id in list(self._host_to_msg_dict):
            ret += self._host_to_msg_dict[host_id]
        self._lock.release_write()
        return ret
