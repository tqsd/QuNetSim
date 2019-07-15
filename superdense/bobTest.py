from cqc.pythonLib import CQCConnection

import sys

sys.path.append("..")

from protocol import protocols


def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        # Receive qubit from Eve

        message = protocols.receive_superdense(Bob)

        to_print = "Receiver {}: The message Alice sent was: {}".format(Bob.name, message)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")


##################################################################################################
main()
