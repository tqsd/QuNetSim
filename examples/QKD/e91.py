from qunetsim.backends import EQSNBackend
from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Logger
from qunetsim.objects import Qubit

import random
import numpy as np

Logger.DISABLED = True

def expected_value(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob, base_alice, base_bob):
    list = [0, 0, 0, 0]

    for i in range(len(result_string_alice)):
        if bases_string_alice[i] == base_alice and bases_string_bob[i] == base_bob:
            if result_string_alice[i] == '0' and result_string_bob[i] == '0':
                list[0] += 1
            elif result_string_alice[i] == '0' and result_string_bob[i] == '1':
                list[1] += 1
            elif result_string_alice[i] == '1' and result_string_bob[i] == '0':
                list[2] += 1
            elif result_string_alice[i] == '1' and result_string_bob[i] == '1':
                list[3] += 1

    return list

def chsh(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob):

    listA1B1 = expected_value(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob, 'a1', 'b1')
    listA1B3 = expected_value(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob, 'a1', 'b3')
    listA3B1 = expected_value(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob, 'a3', 'b1')
    listA3B3 = expected_value(result_string_alice, result_string_bob, bases_string_alice, bases_string_bob, 'a3', 'b3')

    coefA1B1 = (listA1B1[0] - listA1B1[1] - listA1B1[2] + listA1B1[3]) / sum(listA1B1)
    coefA1B3 = (listA1B3[0] - listA1B3[1] - listA1B3[2] + listA1B3[3]) / sum(listA1B3)
    coefA3B1 = (listA3B1[0] - listA3B1[1] - listA3B1[2] + listA3B1[3]) / sum(listA3B1)
    coefA3B3 = (listA3B3[0] - listA3B3[1] - listA3B3[2] + listA3B3[3]) / sum(listA3B3)

    return coefA1B1 - coefA1B3 + coefA3B1 + coefA3B3

def alice(alice, bob, numberOfEntaglementPairs):
    angles = [0, np.pi/4, np.pi/2]
    bases_choice = [random.randint(1,3) for i in range(numberOfEntaglementPairs)]
    test_results_alice = []
    test_bases_alice = []
    sifted_key_alice = []

    for i in range(numberOfEntaglementPairs):

        qubit_a = Qubit(alice)
        qubit_b = Qubit(alice)

        # preparation of singlet state (1/sqrt(2))*(|01> - |10>)
        qubit_a.X()
        qubit_b.X()
        qubit_a.H()
        qubit_a.cnot(qubit_b)

        print('Sending EPR pair %d' % (i + 1))
        _, ack_arrived = alice.send_qubit(bob, qubit_b, await_ack=True)
        if ack_arrived:

            #rotate qubit and measure
            base_a = bases_choice[i]
            qubit_a.rz(angles[base_a-1])
            meas_a = qubit_a.measure()

            ack_arrived = alice.send_classical(bob, base_a, await_ack=True)
            if not ack_arrived:
                print("Send data failed!")

            message = alice.get_next_classical(bob, wait=2)
            if message is not None:
                base_b = message.content

                if (base_a == 2 and base_b == 1) or (base_a == 3 and base_b == 2):
                    sifted_key_alice.append(meas_a)
                elif (base_a == 1 and base_b == 1) or (base_a == 1 and base_b == 3) or (base_a == 3 and base_b == 1) or (base_a == 3 and base_b == 3):
                    test_bases_alice.append('a'+str(base_a))
                    test_results_alice.append(str(meas_a))
            else:
                print("Message doesn't arrivided")
        else:
            print('The EPR pair was not properly established')

    ack_arrived = alice.send_classical(bob, (test_results_alice, test_bases_alice), await_ack=True)
    if not ack_arrived:
        print("Send data failed!")

    print("sifted_key_alice: ", sifted_key_alice)

def bob(bob, alice, numberOfEntaglementPairs):
    angles = [np.pi/4, np.pi/2, 3*(np.pi/4)]
    bob_bases = [random.randint(1,3) for i in range(numberOfEntaglementPairs)]
    test_result_bob = []
    test_bases_bob = []
    sifted_key_bob = []

    for i in range(numberOfEntaglementPairs):
        qubit_b = bob.get_data_qubit(alice, wait=5)
        if qubit_b is not None:
            base_b = bob_bases[i]

            #rotate qubit and measure
            qubit_b.rz(angles[base_b-1])
            meas_b = qubit_b.measure()

            message = bob.get_next_classical(alice, wait=2)
            if message is not None:
                base_a = message.content

                ack_arrived = bob.send_classical(alice, base_b, await_ack=True)
                if not ack_arrived:
                    print("Send data failed!")

                if (base_a == 2 and base_b == 1) or (base_a == 3 and base_b == 2):
                    sifted_key_bob.append(1 - meas_b)
                elif (base_a == 1 and base_b == 1) or (base_a == 1 and base_b == 3) or (base_a == 3 and base_b == 1) or (base_a == 3 and base_b == 3):
                    test_bases_bob.append('b'+str(base_b))
                    test_result_bob.append(str(meas_b))
            else:
                print("Host 2 did not receive the measurement base of alice")
        else:
            print('Host 2 did not receive an EPR pair')

    message = bob.get_next_classical(alice, wait=2)
    if message is not None:
        test_result_alice, test_bases_alice = message.content

        print(chsh(test_result_alice, test_result_bob, test_bases_alice, test_bases_bob))

        print("sifted_key_bob: ", sifted_key_bob)

    else:
        print("Host 2 did not receive the data to compute the chsh value")

def main():
    network = Network.get_instance()

    backend = EQSNBackend()

    numberOfEntaglementPairs = 50

    nodes = ['A', 'B']
    network.start(nodes, backend)
    network.delay = 0.1

    host_A = Host('A', backend)
    host_A.add_connection('B')
    host_A.delay = 0
    host_A.start()

    host_B = Host('B', backend)
    host_B.add_connection('A')
    host_B.delay = 0
    host_B.start()

    network.add_host(host_A)
    network.add_host(host_B)

    t1 = host_A.run_protocol(alice, (host_B.host_id, numberOfEntaglementPairs))
    t2 = host_B.run_protocol(bob, (host_A.host_id, numberOfEntaglementPairs))

    t1.join()
    t2.join()
    network.stop(True)


if __name__ == '__main__':
    main()
