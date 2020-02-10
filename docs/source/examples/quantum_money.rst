Quantum Money with a Man-in-the-Middle Attack
-----------------------------------------------

In this example, we'll see how the Wiesner Quantum Money can be
implemented using QuNetSim. First, we create a network of three different parties:
Alice, Bob, and Eve. In the topology of the network, Alice can talk to Bob and Bob
can talk to Eve. Bob, being the attacker, can modify the qubits to perform an attack.

..  code-block:: python
    :linenos:

    import numpy as np

    # Initialize a network
    network = Network.get_instance()

    # Define the host IDs in the network
    nodes = ['Alice', 'Bob', 'Eve']

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


In this protocol, the aim of the bank is to create unforgeable bank notes
and distribute it to the customers. To achieve this, for every bank note,
the bank assigns a classical serial number and qubits that are polarized in random bases
and random directions. These bases and distributions are recorded
by the bank for later use. In the first part of this example, the bank creates the money
and distributes it to the customer and the customer receives the qubits and the serial numbers:

..  code-block:: python
    :linenos:

    def banker_protocol(host, customer):

        bank_bits = [[] for _ in range(NO_OF_SERIALS)]
        bank_basis = [[] for _ in range(NO_OF_SERIALS)]

        def preparation_and_distribution():
            for serial in range(NO_OF_SERIALS):
                for bit_no in range(QUBITS_PER_MONEY):
                    random_bit = randint(0, 1)
                    random_base = randint(0, 1)

                    bank_bits[serial].append(random_bit)
                    bank_basis[serial].append(random_base)
                    q = Qubit(host)
                    if random_bit == 1:
                        q.X()
                    if random_base == 1:
                        q.H()
                    host.send_qubit(customer, q, True)

    def customer_protocol(host, banker):
        money_qubits = [[] for _ in range(NO_OF_SERIALS)]

        def receive_money():
            for serial in range(NO_OF_SERIALS):
                for bit_no in range(QUBITS_PER_MONEY):
                    q = host.get_data_qubit(banker, wait=10)
                    money_qubits[serial].append(q)

After distributing the money, the customer possesses the money. To use this money, the customer
has to get it verified by the bank. To do this, he sends the serial number of the banknote that
he wants to use along with the qubits assigned to the banknote:

..  code-block:: python
    :linenos:

    def verify_money():
        serial_of_money_to_be_used = randint(0, NO_OF_SERIALS - 1)
        host.send_classical(banker, serial_of_money_to_be_used)

        for qubit_no in range(QUBITS_PER_MONEY):
            host.send_qubit(banker, money_qubits[serial_of_money_to_be_used][qubit_no], await_ack=True)

After receiving the qubits associated with the serial number, the bank measures the qubits to check
if measurement results match with the data in bank's database. If there is a mismatch, the bank realizes
that there is a cheating attempt. If measurement results are correct, the bank verifies the money.

..  code-block:: python
    :linenos:

    def controlling():
    cheat_alert = False
    messages = host.get_classical(customer, wait=10)
    print('SERIAL RECEIVED')
    serial_to_be_checked = messages[-1].content

    for qubit_no in range(QUBITS_PER_MONEY):
        q = host.get_data_qubit(customer, wait=10)

        if bank_basis[serial_to_be_checked][qubit_no] == 1:
            q.H()

        measurement = q.measure()
        if measurement != bank_bits[serial_to_be_checked][qubit_no]:
            print('CHEATING!')
            cheat_alert = True

    if not cheat_alert:
        print('MONEY IS VALID')

If Bob, being the relay node, is an attacker, he can only steal the money but can't reproduce
the money as he doesn't know the polarization bases. Therefore, the money is unforgeable. Also, if
he measures the qubits in a non-destructive way, he can disturb the state of the qubits, therefore
invalidating the money. In this example, an example attack is shown. Bob measures the qubits in a
while relaying the qubits causing the money that is transferred to the customer to be invalid. This attack is
shown below:

..  code-block:: python
    :linenos:

    def bob_sniffing_quantum(sender, receiver, qubit):
    """
    Function to set what the relay node does to the qubit in transmission.

    Args:
        sender (Host) : Sender of the qubit
        receiver (Host) : Receiver of the qubit
        qubit (Qubit): Qubit in transmission
    """

    # Bob measures all qubits that are routed through him in a non-destructive way.
    qubit.measure(True)


The full example is below:

..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from components.logger import Logger
    from objects.qubit import Qubit
    from random import randint

    Logger.DISABLED = True

    WAIT_TIME = 10
    QUBITS_PER_MONEY = 10
    NO_OF_SERIALS = 2


    def banker_protocol(host, customer):
        """
        The banker's protocol.
        Args:
            host (Host): The Host that runs the banker's protocol.
            customer: The ID of the customer.

        """
        bank_bits = [[] for _ in range(NO_OF_SERIALS)]
        bank_basis = [[] for _ in range(NO_OF_SERIALS)]

        def preparation_and_distribution():
            for serial in range(NO_OF_SERIALS):
                for bit_no in range(QUBITS_PER_MONEY):
                    random_bit = randint(0, 1)
                    random_base = randint(0, 1)

                    bank_bits[serial].append(random_bit)
                    bank_basis[serial].append(random_base)
                    q = Qubit(host)
                    if random_bit == 1:
                        q.X()
                    if random_base == 1:
                        q.H()
                    host.send_qubit(customer, q, True)

        def controlling():
            """
            Function to check if qubits representing the money are correct.
            :return: Prints out if the money is valid or if teh customer is cheating.
            """
            cheat_alert = False
            messages = host.get_classical(customer, wait=10)
            print('SERIAL RECEIVED')
            serial_to_be_checked = messages[-1].content

            for qubit_no in range(QUBITS_PER_MONEY):
                q = host.get_data_qubit(customer, wait=10)

                if bank_basis[serial_to_be_checked][qubit_no] == 1:
                    q.H()

                measurement = q.measure()
                if measurement != bank_bits[serial_to_be_checked][qubit_no]:
                    print('CHEATING!')
                    cheat_alert = True
                    break

            if not cheat_alert:
                print('MONEY IS VALID')

        print("Banker is preparing and distributing qubits")
        preparation_and_distribution()
        print("Banker is verifying the money from customer")
        controlling()


    def customer_protocol(host, banker):
        """
        The customer's  protocol.

        Args:
            host (Host): The host who is acting as a customer.
            banker (str): The ID of the banker Host.
        """
        money_qubits = [[] for _ in range(NO_OF_SERIALS)]

        def receive_money():
            for serial in range(NO_OF_SERIALS):
                for bit_no in range(QUBITS_PER_MONEY):
                    q = host.get_data_qubit(banker, wait=10)
                    money_qubits[serial].append(q)

        def verify_money():
            serial_of_money_to_be_used = randint(0, NO_OF_SERIALS - 1)
            host.send_classical(banker, serial_of_money_to_be_used)

            for qubit_no in range(QUBITS_PER_MONEY):
                host.send_qubit(banker, money_qubits[serial_of_money_to_be_used][qubit_no], await_ack=True)

        print('Customer is awaiting serial number and qubits that represent the money')
        receive_money()
        print('Customer is getting his money verified')
        verify_money()


    def bob_sniffing_quantum(sender, receiver, qubit):
        """
        Function to set what the relay node does to the qubit in transmission.

        Args:
            sender (Host) : Sender of the qubit
            receiver (Host) : Receiver of the qubit
            qubit (Qubit): Qubit in transmission
        """

        # Bob measures all qubits that are routed through him in a non-destructive way.
        qubit.measure(True)


    def main():
        # Initialize a network
        network = Network.get_instance()

        nodes = ['Alice', 'Bob', 'Eve']
        network.delay = 0.0
        network.start(nodes)

        host_alice = Host('Alice')
        host_alice.add_connection('Bob')
        host_alice.start()

        host_bob = Host('Bob')
        host_bob.add_connection('Alice')
        host_bob.add_connection('Eve')
        host_bob.start()

        host_eve = Host('Eve')
        host_eve.add_connection('Bob')
        host_eve.start()

        network.add_host(host_alice)
        network.add_host(host_bob)
        network.add_host(host_eve)

        host_bob.quantum_relay_sniffing = True
        host_bob.set_quantum_relay_sniffing_function(bob_sniffing_quantum)

        print('Starting transfer')
        t1 = host_alice.run_protocol(banker_protocol, (host_eve.host_id,))
        t2 = host_eve.run_protocol(customer_protocol, (host_alice.host_id,))

        t1.join()
        t2.join()

        network.stop(True)


    if __name__ == '__main__':
        main()
