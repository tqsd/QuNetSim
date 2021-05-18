#This example implements the B92 QKD protocol in QuNetSim

import numpy as np
from qunetsim.components import Host, Network
from qunetsim.objects import Qubit, Logger
from qunetsim.backends import EQSNBackend
from random import randint

Logger.DISABLED = True

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
        host_eve.quantum_relay_sniffing = True
        host_eve.set_quantum_relay_sniffing_function(eve_sniffing_quantum)
    
    hosts = [host_alice,host_bob,host_eve]

    return network, hosts
    #and Eve might eavesdrop

def generate_key(key_length):
    #generate an encrypted key of a certain length
    generated_key = []
    for i in range(key_length):
        generated_key.append(randint(0,1))
    return generated_key

def sender_qkd(alice, msg_buff, secret_key, receiver):
    #Alice sends the key to Bob
    #the key is an array of binary numbers
    sequence_nr = 0
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
            message = alice.get_next_classical_message(receiver,msg_buff,sequence_nr)
            if message == '1:rectilinear' or '1:diagonal':
                success = True
                #and we can move on and send the next qubit
            sequence_nr += 1
        
def receiver_qkd(bob, msg_buff, key_size, sender):
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
            if base == 1:
                qubit.H()
            bit = qubit.measure()
            if bit == 0:
                message_to_send = 'failed to acquire a qubit'
            elif bit == 1:
                if base == 1:
                    message_to_send = '1:diagonal'
                    resulting_key_bit = 0
                elif base == 0:
                    message_to_send = '1:rectilinear'
                    resulting_key_bit = 1
                key_array.append(resulting_key_bit)  
            bob.send_classical(sender,message_to_send, await_ack = True)  
            sequence_nr += 1 #total counter of transactions



def check_key_sender(alice, msg_buff, lenght_of_check, receiver):
    pass

def check_key_receiver(bob, msg_buff, length_of_check,sender):
    pass

def eve_sniffing_quantum(sender,receiver,qubit):
    base = randint(0,1)
    if base == 1:
        qubit.H()
        #measure the qubit in the diagonal basis basis
        qubit.measure()
    elif base == 0:
        #measure the qubit in the rectilinear basis
        qubit.measure()

def alice_func(alice, bob, length_of_check, key_length):
    #generate the encrypted key
    encryption_key_binary = generate_key(key_length)
    msg_buff = []
    for item in encryption_key_binary:
        sender_qkd(alice, msg_buff, encryption_key_binary, bob.host_id)
        check_key_sender(alice, msg_buff, length_of_check,bob.host_id)
        #what do these function return, if at all? 

def bob_func(bob, alice, length_of_check, key_length):
    msg_buff = []
    receiver_qkd(bob, msg_buff, key_length, alice.host_id)
    check_key_receiver(bob, msg_buff, length_of_check, alice.host_id)

def b92_protocol(eve_interception, key_length, length_of_check):
    network, hosts = build_network_b92(eve_interception)
    host_alice = hosts[0]
    host_bob = hosts[1]
    thread_1 = hosts[0].run_protocol(alice_func,(key_length,length_of_check, host_bob))
    #the protocol for Alice and for Bob should receive the length of the encrypted key, 
    # and the instance of the second host
    thread_2 = hosts[1].run_protocol(bob_func,(key_length, length_of_check, host_alice))

    thread_1.join()
    thread_2.join()


if __name__ == '__main__':
    key_length = 15
    length_of_check = round(key_length/3)
    #the length of the encrypted key
    eve_interception = True
    #whether or not Eve eavesdrops on the quantum channel
    b92_protocol(eve_interception, key_length, length_of_check)
