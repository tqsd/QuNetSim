from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    network.start()
    network.delay = 0.2
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

        q_size=10
        alice_bit_arr = np.random.randint(2,size=q_size)
        alice_base_arr = np.random.randint(2,size=q_size) #0 represents X basis , 1 represents Z basis


        alice_q_arr = []
        for i in range(q_size) :
            alice_q_arr.append(qubit(Alice))
            if alice_bit_arr[i] == 1:
                alice_q_arr[i].X()
            if alice_base_arr[i] == 1:
                 alice_q_arr[i].H()


        for i in range(q_size):
            host_alice.send_qubit( host_bob.host_id , alice_q_arr[i])

        time.sleep(3)

        bob_bit_arr = []
        bob_base_arr = np.random.randint(2,size=q_size)


        for i in range(q_size):
            q = host_bob.get_data_qubit( host_alice.host_id )
            if bob_base_arr[::-1][i] == 1:
                q['q'].H()
            bob_bit_arr.append(q['q'].measure())

        bob_bit_arr = np.asarray(bob_bit_arr [::-1])

        host_bob.send_classical(host_alice.host_id, str(bob_base_arr))
        time.sleep(1)
        message = host_alice.classical[0]['message']
        message_edited = np.fromstring(message[1:-1], dtype=np.int, sep=' ')
        alice_check = []

        for i in range(q_size):
            if alice_base_arr[i] == message_edited[i]: #1 means they have chosen the correct base and 0 otherwise.
                alice_check.append(i)

        alice_check = np.asarray(alice_check)
        host_alice.send_classical(host_bob.host_id, str(alice_check))
        time.sleep(1)
        message_2 = host_bob.classical[0]['message']
        message_2_edited=np.fromstring(message_2[1:-1], dtype=np.int, sep=' ')

        bob_reveal_arr_pos = np.random.randint(2,size=len(message_2_edited))
        bob_reveal_bit = []
        count=0
        i=0
        for i in range(q_size):
            if count < len(message_2_edited) and i == message_2_edited[count]:
                if bob_reveal_arr_pos[count] == 1:
                    bob_reveal_bit.append(bob_bit_arr[i])
                    count = count + 1
                else:
                    bob_reveal_bit.append(2)
                    count=count+1
            else:
                bob_reveal_bit.append(2)

        bob_reveal_bit = np.asarray(bob_reveal_bit)
        host_bob.send_classical(host_alice.host_id, str(bob_reveal_bit))
        time.sleep(1)
        message_3 = host_alice.classical[1]['message']
        message_3_edited = np.fromstring(message_3[1:-1], dtype=np.int, sep=' ')

        alice_confirmation = True
        for i in range(q_size):
            if message_3_edited[i] == 0 or message_3_edited[i] == 1:
                if message_3_edited[i] != alice_bit_arr[i]:
                    alice_confirmation = False

        alice_shared_key = []
        if alice_confirmation == True :
            for i in range(len(alice_check)):
                alice_shared_key.append(alice_bit_arr[(alice_check[i])])

        host_alice.send_classical(host_bob.host_id , str(alice_confirmation))
        time.sleep(1)
        message_4 = host_bob.classical[1]['message']
        bob_shared_key = []
        if message_4 == 'True':
            for i in range(len(alice_check)):
                bob_shared_key.append(bob_bit_arr[(message_2_edited[i])])



        print('alice base arr')
        print(alice_base_arr)
        print('bob base arr')
        print(bob_base_arr)
        print('alice bit_arr')
        print(alice_bit_arr)
        print('bob bit arr')
        print(bob_bit_arr)
        print('message_edited')
        print(message_edited)
        print('message_edited[0]')
        print(message_edited[0])
        print('alice_check')
        print(alice_check)
        print('message 2_edited')
        print(message_2_edited)
        print('len message 2_edited')
        print(len(message_2_edited))
        print('bob reveal arr_pos')
        print(bob_reveal_arr_pos)
        print('test')
        print(message_2_edited[0])
        print('bob_reveal_bit')
        print(bob_reveal_bit)
        print('message3')
        print(message_3_edited)
        print('message3')
        print(message_3_edited[1])
        print('alice confirmation')
        print(alice_confirmation)
        print('alice_shared_key')
        print(alice_shared_key)
        print('message_4')
        print(message_4)
        print('bob shared key')
        print(bob_shared_key)



        nodes = [host_alice, host_bob]

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        for h in nodes:
            h.stop()
        network.stop()


main()
