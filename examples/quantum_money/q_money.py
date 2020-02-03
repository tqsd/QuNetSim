import sys
import time
import numpy as np
import random
from random import randint, random, sample

sys.path.append("../..")
from components.host import Host
from components.network import Network
from objects.daemon_thread import DaemonThread
from objects.qubit import Qubit

wait_time = 10

from components.logger import Logger

#Logger.DISABLED = True

qubit_per_money = 10
no_of_serials = 2

def bank(host, user):
    bank_bits = [[] for i in range(no_of_serials)]
    bank_basis = [[] for j in range(no_of_serials)]

    def preparation_and_distribution():
        for serial in range(no_of_serials):
            for bit_no in range(qubit_per_money):
                random_bit = randint(0, 1)
                random_base = randint(0, 1)

                bank_bits[serial].append(random_bit)
                bank_basis[serial].append(random_base)

                q = Qubit(host)

                if random_bit == 1:
                    q.X()

                if random_base == 1:
                    q.H()

                host.send_qubit(user, q, True)

    def controlling():
        cheat_alert=False
        messages = host.get_classical(user,wait=10)
        print('SERIAL RECEIVED')
        print(messages[-1].content)
        serial_to_be_checked = messages[-1].content

        for qubit_no in range(qubit_per_money):
            q = host.get_data_qubit(user, wait=10)

            if bank_basis[serial_to_be_checked][qubit_no] == 1:
                q.H()

            measurement = q.measure()
            if measurement != bank_bits[serial_to_be_checked][qubit_no]:
                print('CHEATING!')
                cheat_alert = True

        if not cheat_alert:
            print('MONEY IS VALID')

    preparation_and_distribution()
    controlling()

def money_user(host, bank):
    money_qubits = [[] for i in range(no_of_serials)]
    def receive_money():
        for serial in range(no_of_serials):
            for bit_no in range(qubit_per_money):
                q = host.get_data_qubit(bank, wait=10)
                money_qubits[serial].append(q)

    def verify_money():
        serial_of_money_to_be_used = randint(0, no_of_serials-1)
        host.send_classical(bank,serial_of_money_to_be_used)

        for qubit_no in range(qubit_per_money):
            host.send_qubit(bank,money_qubits[serial_of_money_to_be_used][qubit_no],True)

    receive_money()
    verify_money()


def main():
    # Create EQSN backend

    # Initialize a network
    network = Network.get_instance()

    # Define the host IDs in the network
    nodes = ['Alice', 'Bob', 'Eve']

    network.delay = 0.0

    # Start the network with the defined hosts
    network.start(nodes)

    # Initialize the host Alice
    host_alice = Host('Alice')

    # Add a one-way connection (classical and quantum) to Bob
    host_alice.add_connection('Bob')

    # Start listening
    host_alice.start()

    host_bob = Host('Bob')
    # Bob adds his own one-way connection to Alice and Eve
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.start()

    # Add the hosts to the network
    # The network is: Alice <--> Bob <--> Eve
    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)

    hosts = {'Alice': host_alice,
             'Bob': host_bob,
             'Eve': host_eve}

    t1 = host_alice.run_protocol(bank, (host_eve.host_id , ))
    t2 = host_eve.run_protocol(money_user, (host_alice.host_id , ))

    t1.join()
    t2.join()

    for h in hosts.values():
        h.stop()
    network.stop()

if __name__ == '__main__':
    main()
