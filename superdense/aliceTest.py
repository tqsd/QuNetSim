from cqc.pythonLib import CQCConnection
from protocol.protocols import send_superdense


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        message = '11'
        to_print = "The message Alice sent was: {}".format(message)
        print('')
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")
        send_superdense(Alice, message, 'Bob')


##################################################################################################
main()
