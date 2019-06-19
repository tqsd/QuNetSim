
from cqc.pythonLib import CQCConnection, qubit


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        
        qB=Bob.recvQubit()
        qA=Bob.recvQubit()

        qA.cnot(qB)
        qA.H()

        a=qA.measure()
        b=qB.measure()

        to_print = "App {}: Measurement outcomes are: a={}, b={}".format(Bob.name, a, b)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

##################################################################################################
main()




