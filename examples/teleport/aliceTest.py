from cqc.pythonLib import CQCConnection, qubit
import sys

sys.path.append("..")
from components import protocols


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        q = qubit(Alice)
        q.H()

        Alice.sendClassical('Bob', [2])

        protocols.teleport(Alice, 'Bob', q)



        print('Alice: done teleport')


##################################################################################################
main()
