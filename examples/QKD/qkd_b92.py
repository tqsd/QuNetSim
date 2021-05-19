#This example implements the B92 QKD protocol in QuNetSim

import numpy as np
from qunetsim.components import Host, Network
from qunetsim.objects import Message
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
from random import randint

Logger.DISABLED = True
wait_time = 5

def eve_sniffing_quantum(sender,receiver,qubit):
    base = randint(0,1)
    if base == 1:
        qubit.H()
    qubit.measure()

def build_network_b92(eve_interception):
    #this function builds the network for the b92 protocol

    network = Network.get_instance()

    nodes = ['Alice','Bob','Eve']
    network.start(nodes)

    host_alice = Host('Alice')
    host_bob = Host('Bob')
    host_eve = Host('Eve')

    #adding the connections - Alice wants to transfer an encrypted message to Bob
    #Alice---Eve---Bob

    host_alice.add_connection('Eve')
    host_eve.add_connection('Alice')
    host_eve.add_connection('Bob')
    host_bob.add_connection('Eve')

    #starting
    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    if eve_interception == True:
        #if it's true, then Eve is eavesdropping and measuring all the qubits being transferred
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_sniffing_quantum
        #There is some syntax problem with this - asked on Discord.
    
    hosts = [host_alice,host_bob,host_eve]

    print('Made a network!')

    return network, hosts
    #and Eve might eavesdrop

def generate_key(key_length):
    #generate an encrypted key of a certain length
    generated_key = []
    for i in range(key_length):
        generated_key.append(randint(0,1))
    print(f'Generated the key {generated_key}')
    return generated_key

def sender_qkd(alice, msg_buff, secret_key, receiver):
    #Alice sends the key to Bob
    #the key is an array of binary numbers
    sequence_nr = 0
    sent_qubit_counter = 0
    for bit in secret_key:
        success = False
        while not success:
            qubit = Qubit(alice)
            if bit == 1:
                qubit.H()
            #there is no random choice of basis here.
            #If we want to send 0, we'll send |0>
            #If we want to send 1, we'll send |+>
            alice.send_qubit(receiver, qubit, await_ack = True)
            #get a message from Bob whether he measured a "1" in rectilinear basis or a "-" in diagonal basis
            message = alice.get_classical(receiver, seq_num = sequence_nr, wait = wait_time)
            while message == None:
                message = alice.get_classical(receiver, seq_num = sequence_nr, wait = wait_time)
            print(f'message is {message}')

            if message.content == 'qubit successfully acquired':
                success = True
                sent_qubit_counter += 1
                print(f'Sent a qubit {sent_qubit_counter} to Bob successfully!')

                #and we can move on and send the next qubit
            sequence_nr += 1
        
def receiver_qkd(bob, key_size, sender):
    sequence_nr = 0
    key_array = []
    received_counter = 0
    t_wait = 5

    while received_counter < key_size:
        #while we haven't received all the bits of the key successfully
        base = randint(0,1)
        #receive qubit from Alice
        qubit = bob.get_data_qubit(sender,wait = t_wait)
        
        while qubit is None:
            qubit = bob.get_data_qubit(sender, wait = t_wait)

        print(f'Received qubit {sequence_nr} and it\'s of the type {type(qubit)}!')
        if base == 1:
            qubit.H()
        bit = qubit.measure()
        if bit == 0:
            message_to_send = 'failed to acquire a qubit'
        elif bit == 1:
            if base == 1:
                resulting_key_bit = 0
            elif base == 0:
                resulting_key_bit = 1
            message_to_send = 'qubit successfully acquired'
            key_array.append(resulting_key_bit)  
        bob.send_classical(sender,message_to_send, await_ack = True)  
        sequence_nr += 1 #total counter of transactions
    return key_array

def check_key_sender(alice, msg_buff, key_check_alice, receiver):
    for bit in key_check_alice:
        sequence_nr = 0
        cntr = 0
        eavesdropping = False
        msg_buff = []
        len_check = len(key_check_alice)
        while (cntr < len_check) and (eavesdropping == False):
            alice.send_classical(receiver, key_check_alice[cntr], await_ack = True)
            message_from_bob = alice.get_classical(receiver,seq_num = sequence_nr, wait = wait_time)
            if message_from_bob.content == 'fail':
                eavesdropping = True
            cntr += 1
            sequence_nr += 1
        if eavesdropping == False:
            return 'key successfully checked'
            print('Key successfully checked')
        else:
            return 'key was corrupted by Eve'
            print('key corrupted by Eve!')

def check_key_receiver(bob, key_check_bob,sender):
    cntr = 0
    msg_buff = []
    eavesdropping = False
    sequence_nr = 0
    key_check_length = len(key_check_bob)
    while (cntr < key_check_length) and (eavesdropping == False):
        bit_from_alice = bob.get_classical(sender, seq_num = sequence_nr, wait = wait_time)
        if bit_from_alice.content == key_check_bob[cntr]:
            bob.send_classical(sender,'success',await_ack = True)
        else:
            bob.send_classical(sender,'fail',await_ack = True)
            eavesdropping = True
        sequence_nr += 1
        cntr += 1

def alice_func(host, bob_id, length_of_check, key_length):
    #generate the encrypted key
    encryption_key_binary = generate_key(key_length)
    msg_buff = []
    for item in encryption_key_binary:
        sender_qkd(host, msg_buff, encryption_key_binary, bob_id)

    print('Sent all the qubits sucessfully!')

    key_to_test = encryption_key_binary[0:(length_of_check-1)]
    print(f'Alice\'s key is {key_to_test}')
    check_key_sender(host, msg_buff, key_to_test ,bob_id)
        #what do these function return, if at all? 

def bob_func(host, alice_id, length_of_check, key_length):
    secret_key_bob = receiver_qkd(host, key_length, alice_id)
    print(f'Bob\'s key is {secret_key_bob}')
    key_to_test = secret_key_bob[0:(length_of_check-1)]
    message = check_key_receiver(host, key_to_test, alice_id)
    print(message)
    #the message contains whether we successfully transferred the key
    #or whether eavesdropping occurred

def b92_protocol(eve_interception, key_length, length_of_check):
    network, hosts = build_network_b92(eve_interception)
    host_alice = hosts[0]
    host_bob = hosts[1]
    bob_id = host_bob.host_id
    thread_1 = host_alice.run_protocol(alice_func,(bob_id, length_of_check, key_length))
    #the protocol for Alice and for Bob should receive the length of the encrypted key, 
    # and the instance of the second host
    alice_id = host_alice.host_id
    thread_2 = host_bob.run_protocol(bob_func,(alice_id, length_of_check, key_length))

    thread_1.join()
    thread_2.join()

    network.stop(True)
    exit()

if __name__ == '__main__':
    key_length = 3
    length_of_check = round(key_length/3)
    #the length of the encrypted key
    eve_interception = True
    #whether or not Eve eavesdrops on the quantum channel
    b92_protocol(eve_interception, key_length, length_of_check)
