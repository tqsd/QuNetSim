from cqc.pythonLib import CQCConnection, qubit
import sys
import time
import numpy as np
import threading

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

            print('alice bit arr')
            print(alice_bit_arr)
            print('alice base arr')
            print(alice_base_arr)

            for i in range(q_size):
                 host_alice.send_qubit(host_bob.host_id, alice_q_arr[i])

            time.sleep(10)
            alice_messages = host_alice.classical
            print('message len')
            print(len(alice_messages))
            # time.sleep(30)
            # message = host_alice.classical
            #print('test')
            #print(test)
            #print('message')
            #print(message)
            #while message == test:
                #message = host_alice.classical
            #print('message')
            #print(message)

            return

        def qkd_Bob():

            bob_bit_arr = []
            bob_base_arr = np.random.randint(2, size=q_size)

            for i in range(q_size):
                q = host_bob.get_data_qubit(host_alice.host_id)
                while q is None:
                    q = host_bob.get_data_qubit(host_alice.host_id)
                #time.sleep(1)
                if bob_base_arr[::-1][i] == 1:
                    q['q'].H()
                bob_bit_arr.append(q['q'].measure())

            bob_bit_arr = np.asarray(bob_bit_arr[::-1])

            time.sleep(1)
            print('bob base arr')
            print(bob_base_arr)
            print('bob bit arr')
            print(bob_bit_arr)
            host_bob.send_classical(host_alice.host_id, str(bob_base_arr))
            print('message sent')
            time.sleep(1)


            return


        #qkd_Alice()
        #time.sleep(3)
        #qkd_Bob()
        thread_Bob = threading.Thread(target=qkd_Bob())
        thread_Alice = threading.Thread(target=qkd_Alice())

        thread_Bob.start()
        thread_Alice.start()




        nodes = [host_alice, host_bob]

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        for h in nodes:
            h.stop()
        network.stop()


main()
