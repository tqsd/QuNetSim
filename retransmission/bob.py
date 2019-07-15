from cqc.pythonLib import CQCConnection
import random


def main():
    # Initialize the connection
    with CQCConnection("Bob") as Bob:
        success_prob = 0.5
        q_array = []
        k = True
        c = 0
        while k and c < 10:
            q = Bob.recvQubit(block=True)
            if random.random() <= success_prob:
                k = False
                m = q.measure()
                print('Bob: received qubit: ', m)
                Bob.sendClassical('Alice', [1], False)
            else:
                print("Bob: didn't receive the qubit")
                Bob.sendClassical('Alice', [0], False)
                q_array.append(q)
            c += 1

        if c == 10:
            print("Bob: too many attempts made")

        # Remove unused qubits from the system
        for q in q_array:
            q.measure()


main()
