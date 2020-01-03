import sys

sys.path.append("../..")
from objects.classical_storage import *
from objects.message import Message
import components.protocols as protocols

def test_deleting_ACK_messages():
    storage = ClassicalStorage()
    print("Test deleting ACK messages...")
    assert len(storage.get_all()) == 0

    ack_msg = Message("Alice", protocols.ACK, 1)
    storage.add_msg_to_storage(ack_msg)

    assert len(storage.get_all()) == 1

    storage.remove_all_ack("Bob")

    assert len(storage.get_all()) == 1
    storage.remove_all_ack()

    assert len(storage.get_all()) == 0
    print("Test was successfull!")

def test_next_message():
    storage = ClassicalStorage()
    print("Start next message test...")
    assert len(storage.get_all()) == 0
    
    for c in range(15):
        msg = Message("Alice", str(c), c)
        storage.add_msg_to_storage(msg)

    for c in range(15):
        msg = storage.get_next_from_sender("Alice")
        assert msg.content == str(c)
    print("Test was successfull!")


if __name__ == "__main__":
    test_deleting_ACK_messages()
    test_next_message()
