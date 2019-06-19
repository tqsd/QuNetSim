

from cqc.pythonLib import CQCConnection, qubit


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("Eve") as Eve:

        qA = qubit(Eve)
        qB = qubit (Eve)
        qA.H()
        qA.cnot(qB)	
        Eve.sendQubit(qA, "Alice")
        Eve.sendQubit(qB,"Bob")

	    

##################################################################################################
main()
