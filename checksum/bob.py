from cqc.pythonLib import CQCConnection, qubit


def main():
    with CQCConnection("Bob") as Bob:

        q1 = Bob.recvQubit()
        q2 = Bob.recvQubit()
        q3 = Bob.recvQubit()
        q4 = Bob.recvQubit()

        check1 = Bob.recvQubit()
        check2 = Bob.recvQubit()

        q1.cnot(check1)
        q2.cnot(check1)
        q3.cnot(check2)
        q4.cnot(check2)

        m1 = check1.measure()
        print('measured 1')
        m2 = check2.measure()
        print('measured 2')

        if m1 == 0 and m2 == 0:
            print('No error')
        else:
            print('error')

        q1.measure()
        q2.measure()
        q3.measure()
        q4.measure()


main()
