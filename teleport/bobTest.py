from cqc.pythonLib import CQCConnection
import sys

sys.path.append("..")
from protocol import protocols


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        qB = protocols.receive_teleport(Bob)
        m = qB.measure()
        print("Measurement outcome: ", m)


##################################################################################################
main()
