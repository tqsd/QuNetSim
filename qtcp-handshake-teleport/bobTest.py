from cqc.pythonLib import CQCConnection, qubit


def main():

    with CQCConnection("Bob") as Bob:
        #Bob receives the entangled qubits from Eve that are going to be used in teleportation.
        q_teleport_1B = Bob.recvQubit()
        q_teleport_2B = Bob.recvQubit()
        q_teleport_3B = Bob.recvQubit()
        q_teleport_4B = Bob.recvQubit()

        #Bob creates an EPR pair qB_1 and qB_2
        qB_1 = qubit(Bob)
        qB_2 = qubit(Bob)

        qB_1.H()
        qB_1.cnot(qB_2)

        #Bob receives the classical bits from Alice including SYN message and the teleportation bits for qA_2 and decodes the message.
        message_recv_compact = Bob.recvClassical(1,1024,False)
        message_recv = list(message_recv_compact)
        syn_recv = message_recv[0]
        ack_recv = message_recv[1]
        pauli_correct_0 = message_recv[2]
        pauli_correct_1 = message_recv[3]

        #Check is the message is a SYN.
        if syn_recv == 1 and ack_recv == 0:
            print("SYN is received by Bob")

        #Makes the Pauli correction on the teleport_1 to restore the teleported qubit (qA_1).
        if pauli_correct_1 == 1:
            q_teleport_1B.X()
        if pauli_correct_0 == 1:
            q_teleport_1B.Z()

        #Bob measures the two classical bits to send back qA_2 (restored in q_teleport_1B) (using q_teleport_2B) to Alice .
        q_teleport_1B.cnot(q_teleport_2B)
        q_teleport_1B.H()

        a = q_teleport_1B.measure()
        b = q_teleport_2B.measure()

        #Bob measures the two classical bits to send qB_2 (using q_teleport_3B) to Alice .
        qB_2.cnot(q_teleport_3B)
        qB_2.H()

        c = qB_2.measure()
        d = q_teleport_3B.measure()

        syn_send=1
        ack_send=1

        #Sends the SYN-ACK message along with the teleportation bits.
        Bob.sendClassical("Alice", [syn_send, ack_send, a, b, c, d],False)

        #Receives the SYN-ACK message and the teleportation bits for qB_2, then decodes it.
        message_recv_compact = Bob.recvClassical(1,1024,False)
        message_recv = list(message_recv_compact)
        syn_recv = message_recv[0]
        ack_recv = message_recv[1]
        pauli_correct_0 = message_recv[2]
        pauli_correct_1 = message_recv[3]

        if syn_recv == 0 and ack_recv == 1:
            print("ACK is received by Bob.")

        #Makes the Pauli correction on the q_teleport_4B to restore the teleported qubit (qB_2).
        if pauli_correct_1 == 1:
            q_teleport_4B.X()
        if pauli_correct_0 == 1:
            q_teleport_4B.Z()

        #Alice makes a Bell state measurement on qB_1 and qB_2(restored in q_teleport_4B)
        qB_1.cnot(q_teleport_4B)
        qB_1.H()

        measure_1 = qB_1.measure()
        measure_2 = q_teleport_4B.measure()

        #If the measurement results are expected she confirms the TCP connection. If not she raises an error.
        if measure_1 == 0 and measure_2 == 0:
            print("TCP connection is established.")


##################################################################################################
main()
