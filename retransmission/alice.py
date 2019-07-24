from cqc.pythonLib import CQCConnection, qubit


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:
        q = qubit(Alice)
        q.H()

        k = True
        c = 0
        while k and c < 10:
            print('Alice prepares qubit')

            err_1 = qubit(Alice)

            # encode logical qubit
            q.cnot(err_1)

            Alice.sendQubit(q, 'Bob')
            m = list(Alice.recvClassical(1, 1024, False))[0]

            # if ACK
            if m == 1:
                print('Alice: Bob received the qubit')
                # Remove err_1 from simulqron
                err_1.release()
                k = False
            else:
                print('Alice: Bob did not receive the qubit')
                # re-introduce a qubit to the system and correct the error
                q = qubit(Alice)
                err_1.cnot(q)

            c += 1

    if c == 10:
        print("Alice: too many attempts made")


main()
