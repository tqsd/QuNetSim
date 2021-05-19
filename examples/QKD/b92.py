from qunetsim.backends import EQSNBackend
from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Logger
from qunetsim.objects import Qubit

import random
import numpy as np

from itertools import compress

Logger.DISABLED = True

def element_by_indexes(list1, list2, el):
    selectors = [i == el for i in list2]
    return list(compress(list1, selectors))

def protocol_alice(alice, bob, secret_key, sample_len):

    for bit in secret_key:

        q_bit = Qubit(alice)

        if bit == 1:
            q_bit.H()

        alice.send_qubit(bob, q_bit, await_ack=True)

    mes = alice.get_next_classical(bob)
    if mes is not None:
        test = mes.content
        secret_key = element_by_indexes(secret_key, test, 1)

        mes = alice.get_next_classical(bob)
        if mes is not None:
            sample_bob = mes.content

            if sample_bob == secret_key[:sample_len]:
                alice.send_classical(bob, "NO INTERCEPT", await_ack=True)
                print("alice key ", secret_key)
            else:
                alice.send_classical(bob, "EVE IS LISTENING", await_ack=True)
                print("STACCAH STACCAH")

def protocol_bob(bob, alice, key_size, sample_len):
    rcv_cnt = 0
    bit_string = np.random.randint(2, size=key_size)
    test = []

    while rcv_cnt < key_size:

        bit = bit_string[rcv_cnt]

        q_bit = bob.get_data_qubit(alice, wait=2)
        while q_bit is None:
            q_bit = bob.get_data_qubit(alice, wait=2)

        if bit == 1:
            q_bit.H()

        res = q_bit.measure()

        if bit == 0 and res == 1:
            test.append(1)
        elif bit == 1 and res == 1:
            test.append(1)
        else:
            test.append(0)

        rcv_cnt += 1

    bob_key = [1 - el for el in element_by_indexes(bit_string, test, 1)]

    bob.send_classical(alice, test, await_ack=True)

    bob.send_classical(alice, bob_key[:sample_len], await_ack=True)

    mes = bob.get_next_classical(alice)
    if mes is not None:
        if mes.content == "NO INTERCEPT":
            print("bob key ", bob_key)

def eve_intercept_quantum(alice, bob, qubit):

    bit = random.randint(0,1)
    eve_bit_string = []
    if bit == 1:
        qubit.H()
    res = qubit.measure(non_destructive=True)

    if bit == 0 and res == 1:
        print("Intercepted 1")
    elif bit == 1 and res == 1:
        print("Intercepted 0")
    else:
        print("Intercepted -")

def main():

    intercept = True
    key_size = 100
    sample_len = int(key_size/4)

    network = Network.get_instance()
    nodes = ['Alice', 'Eve', 'Bob']
    network.start(nodes)

    host_alice = Host('Alice')
    host_alice.add_connection('Eve')
    host_alice.start()

    host_eve = Host('Eve')
    host_eve.add_connections(['Alice', 'Bob'])
    host_eve.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Eve')
    host_bob.delay = 0.5
    host_bob.start()

    network.add_host(host_alice)
    network.add_host(host_eve)
    network.add_host(host_bob)

    secret_key = np.random.randint(2, size=key_size)

    if intercept:
        host_eve.q_relay_sniffing = True
        host_eve.q_relay_sniffing_fn = eve_intercept_quantum

    t1 = host_alice.run_protocol(protocol_alice, (host_bob.host_id, secret_key, sample_len))
    t2 = host_bob.run_protocol(protocol_bob, (host_alice.host_id, key_size, sample_len))

    t1.join()
    t2.join()
    network.stop(True)


if __name__ == '__main__':
    main()
