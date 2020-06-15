from qunetsim.utils.constants import Constants


class ClassicalStorage(object):
    """
    A classical storage for messages.
    """

    def __init__(self):
        self._host_to_msg_dict = {}
        self._host_to_read_index = {}

    def empty(self):
        """
        Empty the classical storage.
        """
        self._host_to_msg_dict = {}
        self._host_to_read_index = {}

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

        def delete_all_ack_for_sender(sender_id):
            for c, msg in enumerate(self._host_to_msg_dict[sender_id]):
                if msg.content == Constants.ACK:
                    del self._host_to_msg_dict[sender_id][c]

        if from_sender is None:
            for sender in list(self._host_to_msg_dict):
                delete_all_ack_for_sender(sender)
        elif from_sender in self._host_to_msg_dict:
            delete_all_ack_for_sender(from_sender)
        else:
            return

    # TODO: refactor to "add_msg"
    def add_msg_to_storage(self, message):
        """
        Adds a message to the storage.
        """
        sender_id = message.sender
        if sender_id not in list(self._host_to_msg_dict):
            self._add_new_host_id(sender_id)
        self._host_to_msg_dict[sender_id].append(message)

    def get_all_from_sender(self, sender_id, delete=False):
        """
        Get all stored messages from a sender. If delete option is set,
        the returned messages are removed from the storage.

        Args:
            sender_id (String): The host id of the host.
            delete (bool): optional, True if returned messages should be removed from storage.

        Returns:
            List of messages of the sender. If there are none, an empty list is
            returned.
        """
        if delete:
            raise ValueError("delete option not implemented yet!")
        if sender_id in list(self._host_to_msg_dict):
            return self._host_to_msg_dict[sender_id]
        return []

    def get_next_from_sender(self, sender_id):
        """
        Gets the next, unread, message from the sender. If there isn't one,
        None is returned.

        Args:
            sender_id (String): The sender id of the message to get.
        Returns:
            Message object, if such a message exists, or none.
        """
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
        ret = []
        for host_id in list(self._host_to_msg_dict):
            ret += self._host_to_msg_dict[host_id]
        return ret
