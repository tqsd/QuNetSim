import unittest
from qunetsim.objects import ClassicalStorage, Message
from qunetsim.utils.constants import Constants


# @unittest.skip('')
class TestClassicalStorage(unittest.TestCase):
    backends = []

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # @unittest.skip('')
    def test_deleting_ACK_messages(self):
        storage = ClassicalStorage()
        self.assertEqual(len(storage.get_all()), 0)

        ack_msg = Message("Alice", Constants.ACK, 1)
        storage.add_msg_to_storage(ack_msg)

        self.assertEqual(len(storage.get_all()), 1)

        storage.remove_all_ack("Bob")

        self.assertEqual(len(storage.get_all()), 1)
        storage.remove_all_ack()

        self.assertEqual(len(storage.get_all()), 0)

    # @unittest.skip('')
    def test_next_message(self):
        storage = ClassicalStorage()
        self.assertEqual(len(storage.get_all()), 0)

        for c in range(15):
            msg = Message("Alice", str(c), c)
            storage.add_msg_to_storage(msg)

        for c in range(15):
            msg = storage.get_next_from_sender("Alice")
            self.assertEqual(msg.content, str(c))

    # @unittest.skip('')
    def test_message_with_seq_num(self):
        storage = ClassicalStorage()
        self.assertEqual(len(storage.get_all()), 0)

        for c in range(15):
            msg = Message("Alice", str(c), c)
            storage.add_msg_to_storage(msg)

        for c in range(15):
            msg = storage.get_with_seq_num_from_sender("Alice", c)
            self.assertEqual(msg.content, str(c))

        # use new storage
        storage = ClassicalStorage()
        self.assertEqual(len(storage.get_all()), 0)

        for c in range(15):
            msg = Message("Alice", str(c), c)
            storage.add_msg_to_storage(msg)

        for c in range(15):
            msg = storage.get_with_seq_num_from_sender("Alice", c)
            self.assertEqual(msg.content, str(c))
