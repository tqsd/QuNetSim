



class ClassicalStorage(object):

    def __init__(self):
        self._host_to_msg_dict = {}
        self._host_to_read_index = {}

    def _add_new_host_id(self, host_id):
        self._host_to_msg_dict[host_id] = []
        self._host_to_read_index[host_id] = 0

    def remove_all_ack(self, from_sender=None):
        """
        Removes all ACK messages stored. If from sender is given, only ACKs from
        this sender are removed.

        Args:
            from_sender (String): Host id of the sender, whos ACKs should be delted.
        """
        def delete_all_ack_for_sender(sender):
            for c, msg in enumerate(self._host_to_msg_dict[sender]):
                if msg.content == protocols.ACK:
                    del self._host_to_msg_dict[sender][c]

        if from_sender is None:
            for sender in self._host_to_msg_dict.keys():
                delete_all_ack_for_sender(sender)
        else:
            delete_all_ack_for_sender(sender)

    def add_msg_to_storage(self, message):
        """
        Adds a message to the storage.
        """
        sender_id  = message.sender
        if sender_id not in self._host_to_msg_dict.keys():
            self._add_new_host_id(sender_id)
        self._host_to_msg_dict[sender_id].append(message)


    def get_all_from_sender(self, sender_id, delete=False):
        """
        Get all stored messages from a sender.

        Args:
            sender_id (String): The host id of the host.

        Returns:
            List of messages of the sender. If there are none, an empyt list is
            returned.
        """
        if delete:
            raise ValueError("delete option not implemented yet!")
        if sender_id in self._host_to_msg_dict.keys()
            return self._host_to_msg_dict[sender_id]
        return []

    def get_next_from_sender(self, sender_id, delete=False):
        """
        Gets the next, unread, message from the sender. If there isn't one,
        None is returned.

        Args:
            sender_id (String): The sender id of the message to get.

        Returns:
            Message object, if such a message exists, or none.
        """
        if sender_id not in self._host_to_msg_dict.keys():
            return None
        if len(self._host_to_msg_dict[sender_id]) <= self._host_to_read_index[sender_id]:
            return None
        msg = self._host_to_msg_dict[sender_id][self._host_to_read_index[sender_id]]
        self._host_to_read_index[sender_id] += 1
        return msg

    def get_all(self):
        pass
