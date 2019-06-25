from cqc.pythonLib import CQCConnection, qubit


def main():
	# Here Eve acts acts and the entanglement distributor.
	# To start the protocol, Eve sends one half of an entangled pair to Alice
	# and the other to Bob.

    # Initialize the connection
    with CQCConnection("Eve") as Eve:
        qA = qubit(Eve)
        qB = qubit (Eve)

        # Create entanglement between the qubits
        qA.H()
        qA.cnot(qB)

        # Send one half to Alice
        Eve.sendQubit(qA, "Alice")

        # Send one half to Bob
        Eve.sendQubit(qB,"Bob")


##################################################################################################
main()
