import sys

sys.path.append("../..")
from objects.classical_storage import *
from objects.message import Message
import components.protocols as protocols

def test_deleting_ACK_messages():
    storage = ClassicalStorage()

    assert len(storage.get_all()) == 0

    ack_msg = Message("Alice", protocols.ACK, 1)
    storage.add_msg_to_storage(ack_msg)

    assert len(storage.get_all()) == 1

    storage.remove_all_ack("Bob")

    assert len(storage.get_all()) == 1
    storage.remove_all_ack()

    assert len(storage.get_all()) == 0


if __name__ == "__main__":
    test_deleting_ACK_messages()
