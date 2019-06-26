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

        # Create a qubit to teleport
        q = qubit(Alice)

        # Prepare the qubit to teleport in |+>
        q.H()


        # Apply the local teleportation operations
        q.cnot(qA)
        q.H()

        # Measure the qubits
        a = q.measure()
        b = qA.measure()
        to_print = "App {}: Measurement outcomes are: a={}, b={}".format(Alice.name, a, b)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

        # Send corrections to Bob
        Alice.sendClassical("Bob", [a, b])


##################################################################################################
main()
