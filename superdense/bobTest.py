from cqc.pythonLib import CQCConnection
from protocol.protocols import receive_superdense


def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        # Receive qubit from Eve

        message = receive_superdense(Bob)

        to_print = "Receiver {}: The message Alice sent was: {}".format(Bob.name, message)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")


##################################################################################################
main()
