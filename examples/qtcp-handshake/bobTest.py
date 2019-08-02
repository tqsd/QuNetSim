from cqc.pythonLib import CQCConnection, qubit


def main():

    with CQCConnection("Bob") as Bob:

        # Receive the EPR half of Alice and the SYN message
        qB_2 = Bob.recvQubit()

        message_recv_compact = Bob.recvClassical(1, 1024, False)
        message_recv = list(message_recv_compact)
        syn_recv = message_recv[0]
        ack_recv = message_recv[1]

        # Check if message is a SYN.
        if syn_recv == 1 and ack_recv == 0:
            print("SYN is received by Bob")

        # Create an EPR pair.
        qB_3 = qubit(Bob)
        qB_4 = qubit(Bob)
        qB_3.H()
        qB_3.cnot(qB_4)

        # Create a SYN-ACK message.
        syn_send = 1
        ack_send = 1

        # Send half of the EPR pair created (qubit 3) and send back the qubit 2 that Alice has sent first.
        Bob.sendQubit(qB_2, "Alice")
        Bob.sendQubit(qB_3, "Alice")

        # Send SYN-ACK message.
        Bob.sendClassical("Alice", [syn_send, ack_send])

        # Receive the ACK message.
        message_recv_compact = Bob.recvClassical(1, 1024, False)
        message_recv = list(message_recv_compact)
        syn_recv = message_recv[0]
        ack_recv = message_recv[1]

        # Receive the qubit 3.
        qA_3 = Bob.recvQubit()

        # Check if message is a ACK.
        if syn_recv == 0 and ack_recv == 1:
            print("ACK is received by Bob")

        # Make a Bell State measurement in qubit 3 and qubit 4.
        qA_3.cnot(qB_4)
        qA_3.H()
        c = qA_3.measure()
        d = qB_4.measure()

        # If measurement results are as expected , establish the TCP connection.
        # Else report that there is something wrong.
        if c == 0 and d == 0:
            print("TCP connection established.")
        else:
            print("Something is wrong.")

        exit()


##################################################################################################
main()
