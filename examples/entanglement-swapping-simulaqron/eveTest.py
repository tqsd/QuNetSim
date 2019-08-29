from cqc.pythonLib import CQCConnection, qubit


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Eve") as Eve:

        qE = Eve.recvEPR()

        # Receive info about corrections
        data = Eve.recvClassical()
        message = list(data)
        a = message[0]
        b = message[1]

        # Apply corrections
        if b == 1:
            qE.X()
        if a == 1:
            qE.Z()

        # Measure qubit
        m = qE.measure()
        to_print = "App {}: Measurement outcome is: {}".format(Eve.name, m)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")


##################################################################################################
main()
