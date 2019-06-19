

from cqc.pythonLib import CQCConnection, qubit


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        qA = Alice.recvQubit()
        Alice.sendQubit(qA,"Bob")
        #qA = Alice.createEPR( "Bob")
        #qA.Z()	
        #qA.X()	
        #Alice.sendQubit(qA, "Bob")

	    

##################################################################################################
main()
