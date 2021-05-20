#This example implements the B92 QKD protocol using the QuNetSim package

from qunetsim.components import Host, Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
from random import randint, random

Logger.DISABLED = True
wait_time = 60

def eve_sniffing_quantum(sender,receiver,qubit):
    if sender == 'Alice':
        r = random()
        if r > 0.5:
            base = randint(0,1)
            if base == 1:
                qubit.H()
            qubit.measure(non_destructive = True)
            #print('Eve measured a qubit')

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

    host_alice.delay = 0.3
    host_bob.delay = 0.3

    #starting
    host_alice.start()
    host_bob.start()
    host_eve.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    if eve_interception == True:
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

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

def sender_qkd(alice, secret_key, receiver):
    sent_qubit_counter = 0
    for bit in secret_key:
        success = False
        while success == False:
            qubit = Qubit(alice)
            if bit == 1:
                qubit.H()
            #there is no random choice of basis here.
            #If we want to send 0, we'll send |0>
            #If we want to send 1, we'll send |+>
            _, ack = alice.send_qubit(receiver, qubit, await_ack = True)
            message = alice.get_next_classical(receiver, wait = -1)
            if message is not None:
                if message.content == 'qubit successfully acquired':
                    print(f'Alice sent qubit {sent_qubit_counter+1} to Bob')
                    success = True
                    sent_qubit_counter += 1
        
def receiver_qkd(bob, key_size, sender):
    key_array = []
    received_counter = 0

    while received_counter < key_size:
        #while we haven't received all the bits of the key successfully
        base = randint(0,1)
        #receive qubit from Alice
        qubit = bob.get_data_qubit(sender,wait = wait_time)
        if qubit is not None:
            if base == 1:
                qubit.H()
            bit = qubit.measure()
            if bit == 1:
                if base == 1:
                    resulting_key_bit = 0
                elif base == 0:
                    resulting_key_bit = 1
                message_to_send = 'qubit successfully acquired'
                key_array.append(resulting_key_bit) 
                received_counter += 1 
                print(f'Bob received qubit {received_counter}')
            else:
                message_to_send = 'fail'
            bob.send_classical(sender,message_to_send, await_ack = True) 
    return key_array


def check_key_sender(alice, key_check_alice, receiver):
    key_check_string = ''.join([str(x) for x in key_check_alice])
    print(f'Alice\'s key to check is {key_check_string}')
    ack_alice = alice.send_classical(receiver,key_check_string,await_ack = True)

    message_from_bob = alice.get_next_classical(receiver, wait = -1)

    if message_from_bob is not None:
        if message_from_bob.content == 'Success':
            print('Key is successfully verified')
        elif message_from_bob.content == 'Fail':
            print('Key has been corrupted')


def check_key_receiver(bob, key_check_bob,sender):
    key_check_bob_string = ''.join([str(x) for x in key_check_bob])
    print(f'Bob\'s key to check is {key_check_bob_string}')
    key_from_alice = bob.get_next_classical(sender, wait = -1)
    if key_from_alice is not None:
        if key_from_alice.content == key_check_bob_string:
            ack_bob = bob.send_classical(sender,'Success',await_ack = True)
        else:
            ack_bob = bob.send_classical(sender,'Fail',await_ack = True)


def alice_func(host, bob_id, length_of_check, key_length):
    #generate the encrypted key
    encryption_key_binary = generate_key(key_length)
    sender_qkd(host, encryption_key_binary, bob_id)
    print('Sent all the qubits sucessfully!')
    key_to_test = encryption_key_binary[0:length_of_check]
    check_key_sender(host, key_to_test ,bob_id)


def bob_func(host, alice_id, length_of_check, key_length):
    secret_key_bob = receiver_qkd(host, key_length, alice_id)
    key_to_test = secret_key_bob[0:length_of_check]
    check_key_receiver(host, key_to_test, alice_id)


def b92_protocol(eve_interception, key_length, length_of_check):
    network, hosts = build_network_b92(eve_interception)
    host_alice = hosts[0]
    host_bob = hosts[1]
    bob_id = host_bob.host_id
    alice_id = host_alice.host_id

    thread_1 = host_alice.run_protocol(alice_func,(bob_id, length_of_check, key_length,))
    thread_2 = host_bob.run_protocol(bob_func,(alice_id, length_of_check, key_length,))

    thread_1.join()
    thread_2.join()

    network.stop(True)
    exit()


if __name__ == '__main__':
    key_length = 10
    length_of_check = round(key_length/2)
    #the length of the encrypted key
    eve_interception = False
    #whether or not Eve eavesdrops on the quantum channel
    b92_protocol(eve_interception, key_length, length_of_check)
