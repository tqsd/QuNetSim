from cqc.pythonLib import CQCConnection, qubit


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:

        # Create an EPR pair.
        qA_1 = qubit(Alice)
        qA_2 = qubit(Alice)

        qA_1.H()
        qA_1.cnot(qA_2)

        # Create a SYN message.
        syn_send = 1
        ack_send = 0

        # Send a half of EPR pair and the SYN message to Bob.
        Alice.sendQubit(qA_2, "Bob")
        Alice.sendClassical("Bob", [syn_send, ack_send], False)

        # Receive the qubits Bob has sent (qubit 2 and qubit 3) for SYN-ACK.
        qB_2 = Alice.recvQubit()
        qB_3 = Alice.recvQubit()

        # Receive the classical message Bob has sent for SYN-ACK.
        message_recv_compact = Alice.recvClassical(1, 1024, False)
        message_recv = list(message_recv_compact)
        syn_recv = message_recv[0]
        ack_recv = message_recv[1]

        # Check if message is a SYN-ACK.
        if syn_recv == 1 and ack_recv == 1:
            print("SYN-ACK is received by Alice")

        # Make a Bell State measurement on qubit 1 and qubit 2.
        qA_1.cnot(qB_2)
        qA_1.H()
        a = qA_1.measure()
        b = qB_2.measure()

        # If measurement results are as expected , send Bob a ACK message and the qubit 3 that he has sent previously.
        # Else report that there is something wrong.
        if a == 0 and b == 0:
            syn_send = 0
            ack_send = 1
            Alice.sendClassical("Bob", [syn_send, ack_send], False)
            Alice.sendQubit(qB_3, "Bob")
        else:
            print("Something is wrong.")

        exit()


##################################################################################################
main()
