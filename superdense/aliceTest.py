from cqc.pythonLib import CQCConnection, qubit


def main():

    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        qA = Alice.recvQubit()
        Alice.sendQubit(qA,"Bob")
	    

##################################################################################################
main()
