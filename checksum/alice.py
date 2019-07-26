import time

from cqc.pythonLib import CQCConnection, qubit
import sys
import random

sys.path.append("..")
from protocol import protocols


def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:

        # print('Alice sent 0')
        # Alice.sendClassical('Bob', [0])
        # time.sleep(0.5)
        # q = qubit(Alice)
        # Alice.sendQubit(q, 'Bob')
        #
        # time.sleep(0.5)
        # print('Alice sent 1')
        # Alice.sendClassical('Bob', [1])
        # q = Alice.createEPR('Bob')
        # time.sleep(0.5)
        # print('Alice: ', q.measure())

        # Assume Alice wants to send the following 4 qubits to Bob
        q1 = qubit(Alice)
        q2 = qubit(Alice)
        q3 = qubit(Alice)
        q4 = qubit(Alice)

        # encode qubits
        q1.I()
        q2.I()
        q3.I()
        q4.I()

        # generate the checksum qubits with 2 qubits per checksum qubit
        check_qubits = protocols.add_checksum(Alice, [q1, q2, q3, q4], size=2)

        print('Apply error to random qubit with p=0.5')
        if random.random() < 0.5:
            print('error on qubit')
            random.choice([q1, q2, q3, q4]).X()
        else:
            print('no error on qubit')

        print('Alice sends qubits to Bob')

        Alice.sendQubit(q1, 'Bob')
        Alice.sendQubit(q2, 'Bob')
        Alice.sendQubit(q3, 'Bob')
        Alice.sendQubit(q4, 'Bob')
        Alice.sendQubit(check_qubits[0], 'Bob')
        Alice.sendQubit(check_qubits[1], 'Bob')


main()
