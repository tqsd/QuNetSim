from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np
from threading import Thread

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.2
    # network.x_error_rate = 0.5
    #network.packet_drop_rate = 0.5
    print('')

    with CQCConnection("Alice") as Alice, CQCConnection("Bob") as Bob, \
            CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:

        host_alice = Host('00000000', Alice)
        host_alice.add_connection('00000001')
        host_alice.start()

        host_bob = Host('00000001', Bob)
        host_bob.add_connection('00000000')
        host_bob.start()

        network.add_host(host_alice)
        network.add_host(host_bob)

        q_size = 10

        def qkd_Alice():
            alice_bit_arr = np.random.randint(2, size=q_size)
            alice_base_arr = np.random.randint(2, size=q_size)  # 0 represents X basis , 1 represents Z basis
            alice_q_arr = []
            for i in range(q_size):
                alice_q_arr.append(qubit(Alice))
                if alice_bit_arr[i] == 1:
                    alice_q_arr[i].X()
                if alice_base_arr[i] == 1:
                    alice_q_arr[i].H()


            for i in range(q_size):
                host_alice.send_qubit(host_bob.host_id, alice_q_arr[i], True)

            message = host_alice.get_classical(host_bob.host_id, 10)
            while len(message) < q_size + 1:
                message = host_alice.get_classical(host_bob.host_id, 10)

            intended_message = message[-1]['message']

            message_edited = np.fromstring(intended_message[1:-1], dtype=np.int, sep=' ')

            alice_check = []

            for i in range(q_size):
                if alice_base_arr[i] == message_edited[i]:  # 1 means they have chosen the correct base and 0 otherwise.
                    alice_check.append(i)

            alice_check = np.asarray(alice_check)

            host_alice.send_classical(host_bob.host_id, str(alice_check), True)

            message = host_alice.get_classical(host_bob.host_id, 10)
            while len(message) < q_size + 3:
                message = host_alice.get_classical(host_bob.host_id, 10)

            intended_message_2 = message[-1]['message']

            message_3_edited = np.fromstring(intended_message_2[1:-1], dtype=np.int, sep=' ')

            alice_confirmation = True
            i = 0
            for i in range(q_size):
                if message_3_edited[i] == 0 or message_3_edited[i] == 1:
                    if message_3_edited[i] != alice_bit_arr[i]:
                        print(i)
                        print(' is wrong ')
                        alice_confirmation = False

            alice_shared_key = []
            if alice_confirmation == True:
                for i in range(len(alice_check)):
                    alice_shared_key.append(alice_bit_arr[(alice_check[i])])

            print('alice shared key')
            print(alice_shared_key)

            host_alice.send_classical(host_bob.host_id, str(alice_confirmation))


            return

        def qkd_Bob():

            bob_bit_arr = []
            bob_base_arr = np.random.randint(2, size=q_size)

            for i in range(q_size):
                q = host_bob.get_data_qubit(host_alice.host_id, wait=10)
                if bob_base_arr[i] == 1:
                    q['q'].H()
                bob_bit_arr.append(q['q'].measure())

            bob_bit_arr = np.asarray(bob_bit_arr[::-1])
            print(bob_bit_arr)
            time.sleep(1)
            host_bob.send_classical(host_alice.host_id, str(bob_base_arr), True)

            bobs_messages = host_bob.get_classical(host_alice.host_id, 10)
            while len(bobs_messages) < 2:
                bobs_messages = host_bob.get_classical(host_alice.host_id, 10)

            message_2 = host_bob.get_classical(host_alice.host_id, 10)[1]['message']
            message_2_edited = np.fromstring(message_2[1:-1], dtype=np.int, sep=' ')

            bob_reveal_arr_pos = np.random.randint(2, size=len(message_2_edited))
            bob_reveal_bit = []
            bob_bit_arr = bob_bit_arr[::-1]
            count = 0
            for i in range(q_size):
                if count < len(message_2_edited) and i == message_2_edited[count]:
                    if bob_reveal_arr_pos[count] == 1:
                        bob_reveal_bit.append(bob_bit_arr[i])
                        count = count + 1
                    else:
                        bob_reveal_bit.append(2)
                        count = count + 1
                else:
                    bob_reveal_bit.append(2)

            bob_reveal_bit = np.asarray(bob_reveal_bit)
            host_bob.send_classical(host_alice.host_id, str(bob_reveal_bit), True)

            bobs_messages = host_bob.get_classical(host_alice.host_id, 10)
            while len(bobs_messages) < 4:
                bobs_messages = host_bob.get_classical(host_alice.host_id, 10)

            message_4 = bobs_messages[-1]['message']
            bob_shared_key = []

            if message_4 == 'True':
                for i in range(len(message_2_edited)):
                    bob_shared_key.append(bob_bit_arr[(message_2_edited[i])])

            print('bob shared key')
            print(bob_shared_key)

            return

        if __name__ == '__main__':
            Thread(target=qkd_Alice).start()
            Thread(target=qkd_Bob).start()

        nodes = [host_alice, host_bob]

        start_time = time.time()
        while time.time() - start_time < 50:
            pass

        for h in nodes:
            h.stop()
        network.stop()


main()
