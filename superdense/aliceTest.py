from cqc.pythonLib import CQCConnection, qubit


def encode(message, qubit):
    """
    Return a qubit encoded with the message message.

    Params:
    message -- the message to encode
    qubit -- the qubit to encode the message

    """

    if message == '00':
        # do nothing (i.e. perform identity)
        pass
    elif message == '01':
        qubit.X()
    elif message == '10':
        qubit.Z()
    elif message == '11':
        qubit.X()
        qubit.Z()
    else:
        throw("Not possible to encode this message")

    return qubit


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        # Receive qubit from Eve
        qA = Alice.recvQubit()
        encode('11', qA)

        # Send qubit to Bob
        Alice.sendQubit(qA, "Bob")


##################################################################################################
main()
