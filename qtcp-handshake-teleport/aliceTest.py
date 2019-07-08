from cqc.pythonLib import CQCConnection, qubit



def main():
    # Initialize the connection
	with CQCConnection("Alice") as Alice:

		#Alice receives the entangled qubits from Eve that are going to be used in teleportation.

		q_teleport_1A = Alice.recvQubit()
		q_teleport_2A = Alice.recvQubit()
		q_teleport_3A = Alice.recvQubit()
		q_teleport_4A = Alice.recvQubit()

		#Alice creates an EPR pair qA_1 and qA_2

		qA_1 = qubit(Alice)
		qA_2 = qubit(Alice)

		qA_1.H()
		qA_1.cnot(qA_2)

		#Alice measures the two classical bits to send qA_2 (using teleport_1A) to Bob.
		qA_2.cnot(q_teleport_1A)
		qA_2.H()

		a = qA_2.measure()
		b = q_teleport_1A.measure()

		#Alice sends SYN message along with the teleportation bits.
		syn_send=1
		ack_send=0

		Alice.sendClassical("Bob", [syn_send, ack_send, a, b],False)

		#Receives the SYN-ACK message and the teleportation bits for qA_2 and qB_2, then decodes it.
		message_recv_compact = Alice.recvClassical(1,1024,False)
		message_recv = list(message_recv_compact)
		syn_recv = message_recv[0]
		ack_recv = message_recv[1]
		pauli_correct_0 = message_recv[2]
		pauli_correct_1 = message_recv[3]
		pauli_correct_2 = message_recv[4]
		pauli_correct_3 = message_recv[5]

		#Makes the Pauli correction on the q_teleport_2A to restore the teleported qubit (qA_2).
		if pauli_correct_1 == 1 :
			q_teleport_2A.X()
		if pauli_correct_0 == 1:
			q_teleport_2A.Z()

		#Makes the Pauli correction on the q_teleport_3A to restore the teleported qubit (qB_2).
		if pauli_correct_3 == 1:
			q_teleport_3A.X()
		if pauli_correct_2 == 1:
			q_teleport_3A.Z()


		#Alice makes a Bell state measurement on qA_1 and qA_2(restored in q_teleport_2A)
		qA_1.cnot(q_teleport_2A)
		qA_1.H()
		measure_1 = qA_1.measure()
		measure_2 = q_teleport_2A.measure()
		#If the measurement results are expected she continues the protocol. If not she raises an error.
		if measure_1 != 0 and measure_2!= 0:
			print("Something is wrong in Alice's measurement.")
			exit()

		#Check if the message is a SYN-ACK.
		if syn_recv == 1 and ack_recv == 1:
			print("SYN-ACK is received by Alice.")

		#Alice measures the two classical bits to send qB_2(restored in q_teleport_3A) (using teleport_4A) to Bob.
		q_teleport_3A.cnot(q_teleport_4A)
		q_teleport_3A.H()
		e = q_teleport_3A.measure()
		f = q_teleport_4A.measure()

		syn_send=0
		ack_send=1

		#Alice sends ACK message along with the teleportation bits.
		Alice.sendClassical("Bob", [syn_send, ack_send, e, f],False)






##################################################################################################
main()
