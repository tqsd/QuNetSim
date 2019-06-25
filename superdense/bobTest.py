from cqc.pythonLib import CQCConnection, qubit


def decode(qA, qB):
    """
    Return the message encoded into qA with the support of qB.

    Params:
    qA -- the qubit the message is encoded into
    qB -- the supporting entangled pair

    """

    qA.cnot(qB)
    qA.H()

    # Measure
    a = qA.measure()
    b = qB.measure()

    return str(a) + str(b)


def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        # Receive qubit from Eve
        qB = Bob.recvQubit()

        # Receive qubit from Alice
        qA = Bob.recvQubit()

        # Decode message
        message = decode(qA, qB)

        # Print the output of the super dense coding transmission
        to_print = "Receiver {}: The message Alice sent was: {}".format(Bob.name, message)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")


##################################################################################################
main()
