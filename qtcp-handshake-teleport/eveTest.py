from cqc.pythonLib import CQCConnection, qubit


def main():
	# Here Eve acts acts and the entanglement distributor.
	# To start the protocol, Eve sends  halves of the 4 entangled pairs to Alice
	# and and Bob.

    # Initialize the connection
    with CQCConnection("Eve") as Eve:
        q_teleport_A1 = qubit(Eve)
        q_teleport_B1 = qubit (Eve)

        q_teleport_A2 = qubit(Eve)
        q_teleport_B2 = qubit (Eve)

        q_teleport_A3 = qubit(Eve)
        q_teleport_B3 = qubit (Eve)

        q_teleport_A4 = qubit(Eve)
        q_teleport_B4 = qubit (Eve)

        # Create entanglement between the qubits
        q_teleport_A1.H()
        q_teleport_A1.cnot(q_teleport_B1)

        q_teleport_A2.H()
        q_teleport_A2.cnot(q_teleport_B2)

        q_teleport_A3.H()
        q_teleport_A3.cnot(q_teleport_B3)

        q_teleport_A4.H()
        q_teleport_A4.cnot(q_teleport_B4)

        # Send  first halves to Alice
        Eve.sendQubit(q_teleport_A1, "Alice")
        Eve.sendQubit(q_teleport_A2, "Alice")
        Eve.sendQubit(q_teleport_A3, "Alice")
        Eve.sendQubit(q_teleport_A4, "Alice")

        # Send second halves to Bob
        Eve.sendQubit(q_teleport_B1,"Bob")
        Eve.sendQubit(q_teleport_B2,"Bob")
        Eve.sendQubit(q_teleport_B3,"Bob")
        Eve.sendQubit(q_teleport_B4,"Bob")


##################################################################################################
main()
