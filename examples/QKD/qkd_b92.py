#This example implements the B92 QKD protocol in QuNetSim

import numpy as np
from qunetsim.components import Host, Network
from qunetsim.objects import Qubit, Logger
from qunetsim.backends import EQSNBackend

Logger.DISABLED = True

def build_network_b92():
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
    
    hosts = [host_alice,host_bob,host_eve]

    return network, hosts
    #and Eve might eavesdrop

def generate_key(key_length):
    #generate an encrypted key of a certain length
    pass

def send_key(key):
    #Alice sends the key to Bob
    pass

def b92_protocol():
    network, nosts = build_network_b92()

def main():
    #run the b92 protocol function
    b92_protocol()

if __name__ == '__main__':
    main()
