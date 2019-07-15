from cqc.pythonLib import CQCConnection
from protocol.protocols import receive_teleport


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        qB = receive_teleport(Bob)
        m = qB.measure()
        print("Measurement outcome: ", m)


##################################################################################################
main()
