from cqc.pythonLib import CQCConnection, qubit


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("Alice") as Alice:

        # Make an EPR pair with Bob
        qA = Alice.createEPR("Bob")

        # Measure qubit
        m = qA.measure()
        to_print = "App {}: Measurement outcome is: {}".format(Alice.name, m)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

        # # Create a qubit to teleport
        # q = qubit(Alice)
        #
        # # Prepare the qubit to teleport in |+>
        # q.H()
        #
        #
        # # Apply the local teleportation operations
        # q.cnot(qA)
        # q.H()

        # Measure the qubits
        # a = q.measure()
        # b = qA.measure()
        # to_print = "App {}: Measurement outcomes are: a={}, b={}".format(Alice.name, a, b)
        # print("|" + "-" * (len(to_print) + 2) + "|")
        # print("| " + to_print + " |")
        # print("|" + "-" * (len(to_print) + 2) + "|")
        #
        # # Send corrections to Bob
        # Alice.sendClassical("Bob", [a, b])


##################################################################################################
main()
