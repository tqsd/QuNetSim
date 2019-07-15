from cqc.pythonLib import CQCConnection


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:

        # Make an EPR pair with Alice
        qB = Bob.recvEPR()

        # Receive info about corrections
        data = Bob.recvClassical()
        message = list(data)
        a = message[0]
        b = message[1]

        # Apply corrections
        if b == 1:
            qB.X()
        if a == 1:
            qB.Z()

            # Measure qubit
        m = qB.measure()
        to_print = "App {}: Measurement outcome is: {}".format(Bob.name, m)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")


##################################################################################################
main()
