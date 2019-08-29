from cqc.pythonLib import CQCConnection,qubit


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("Bob") as Bob:

        # Make an EPR pair with Alice and Eve
        qB_1 = Bob.recvEPR()
        qB_2 = Bob.createEPR("Eve")

        # Apply the local teleportation operations
        qB_1.cnot(qB_2)
        qB_1.H()

        # #Measure the qubits
        a = qB_1.measure()
        b = qB_2.measure()

        # Send corrections to Eve
        Bob.sendClassical("Eve", [a, b])


##################################################################################################
main()
