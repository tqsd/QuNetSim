from cqc.pythonLib import CQCConnection

import sys

sys.path.append("..")

from protocol import protocols


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        message = '11'

        to_print = "The message Alice sent was: {}".format(message)
        print('')
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

        protocols.send_superdense(Alice, message, 'Bob')


##################################################################################################
main()
