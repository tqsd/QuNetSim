from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("..")
from protocol import protocols


#####################################################################################################
#
# main
#
def main():
    # Initialize the connection
    with CQCConnection("Alice") as Alice:


        what_to_do = protocols.SEND_UDP_PACKET

        if what_to_do == protocols.TELEPORT:
            q = qubit(Alice)
            q.X()
            time.sleep(0.5)
            protocols.teleport(Alice, 'Bob', q)

        if what_to_do == protocols.SUPERDENSE:
            Alice.sendClassical("Bob", [what_to_do])
            message = '10'
            to_print = "The message Alice sent was: {}".format(message)
            print('')
            print("|" + "-" * (len(to_print) + 2) + "|")
            print("| " + to_print + " |")
            print("|" + "-" * (len(to_print) + 2) + "|")

            protocols.send_superdense(Alice, message, 'Bob')

        if what_to_do == protocols.SEND_UDP_PACKET:

            # Generate a random bit array(information) and encode them into qubits
            packet_checksum_ratio = 2
            checksum_size = 5
            packet_size = checksum_size * packet_checksum_ratio
            random_info = np.random.randint(2, size=packet_size)
            print("Here is the random info:")
            print(random_info)

            info_qubits = [None] * packet_size

            for i in range(packet_size):
                info_qubits[i] = qubit(Alice)
                if random_info[i] == 1:
                    info_qubits[i].X()

            check_qubits = protocols.add_checksum(Alice, info_qubits, size=packet_checksum_ratio)

            for i in range(packet_size):
                protocols.teleport(Alice, 'Bob', info_qubits[i])
                time.sleep(0.2)

            for i in range(checksum_size):
                protocols.teleport(Alice, 'Bob', check_qubits[i])
                # print("here")
                time.sleep(0.2)

            what_to_do = protocols.TERMINATE_UDP_PACKET
            time.sleep(0.2)

        if what_to_do == protocols.TERMINATE_UDP_PACKET:
            Alice.sendClassical("Bob", [what_to_do, packet_size, checksum_size])
            return


##################################################################################################
main()
