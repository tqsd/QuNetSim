from cqc.pythonLib import CQCConnection, qubit
from protocol.protocols import teleport


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        q = qubit(Alice)
        teleport(Alice, 'Bob', q)


##################################################################################################
main()
