Quantum Money with a Man-in-the-Middle Attack
-----------------------------------------------

In this example, we'll see how the Wiesner Quantum Money can be
implemented using QuNetSim. First, we create a network of three different parties:
the bank, the customer, and Eve who plays the eavesdropper. In this protocol, the bank talks to the customer but the
information is relayed through Eve, i.e. the "man in the middle". First we Initialize the network:

..  code-block:: python
    :linenos:

    def main():
        # Initialize a network
        network = Network.get_instance()
        nodes = ['Bank', 'Customer', 'Eve']
        network.start(nodes)

        host_bank = Host('Bank')
        host_bank.add_connection('Eve')
        host_bank.start()

        host_eve = Host('Eve')
        host_eve.add_connection('Bank')
        host_eve.add_connection('Customer')
        host_eve.start()

        host_customer = Host('Customer')
        host_customer.add_connection('Eve')
        host_customer.start()

        network.add_host(host_bank)
        network.add_host(host_eve)
        network.add_host(host_customer)


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
                    host.send_qubit(customer, q)


After the bank distributes the money, the customer possesses the money.

..  code-block:: python
    :linenos:

    def customer_protocol(host, banker):
        money_qubits = [[] for _ in range(NO_OF_SERIALS)]

        def receive_money():
            for serial in range(NO_OF_SERIALS):
                for bit_no in range(QUBITS_PER_MONEY):
                    q = host.get_data_qubit(banker, wait=10)
                    money_qubits[serial].append(q)


To use this money, the customer has to get it verified by the bank.
To do this, he sends the serial number of the banknote that
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
        message = host.get_classical(customer, seq_num=0, wait=10)
        serial_to_be_checked = message.content
        for qubit_no in range(QUBITS_PER_MONEY):
            q = host.get_data_qubit(customer, wait=10)
            if bank_basis[serial_to_be_checked][qubit_no] == 1:
                q.H()

            measurement = q.measure()
            if measurement != bank_bits[serial_to_be_checked][qubit_no]:
                cheat_alert = True
                break

        if not cheat_alert:
            print('MONEY IS VALID')

If Eve, being the relay node, acts as an attacker, she can only steal the money but can't reproduce
the money as she doesn't know the polarization bases. Therefore, the money is unforgeable. Also, if
she measures the qubits in a non-destructive way, she can disturb the state of the qubits, therefore
invalidating the money. In this example, an example attack is shown. Eve measures the qubits in a
while relaying the qubits causing the money that is transferred to the customer to be invalid. This attack is
shown below:

..  code-block:: python
    :linenos:

    def sniffing_quantum(sender, receiver, qubit):
        """
        Function to set what the relay node does to the qubit in transmission.

        Args:
            sender (Host) : Sender of the qubit
            receiver (Host) : Receiver of the qubit
            qubit (Qubit): Qubit in transmission
        """

        # Eavesdropper measures some of the qubits.
        if sender == 'Bank' and random() <= 0.25:
            print('Eavesdropper measured qubit from %s to %s' % (sender, receiver))
            qubit.measure(non_destructive=True)


The full example is below:

..  code-block:: python
    :linenos:

    from components.host import Host
    from components.network import Network
    from components.logger import Logger
    from objects.qubit import Qubit
    from random import randint, random
    from backends.projectq_backend import ProjectQBackend

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
                    host.send_qubit(customer, q)

        def controlling():
            """
            Function to check if qubits representing the money are correct.
            :return: Prints out if the money is valid or if teh customer is cheating.
            """
            cheat_alert = False
            print('Banker waiting for serial')
            message = host.get_classical(customer, seq_num=0, wait=10)
            print('Serial received by Bank')
            serial_to_be_checked = message.content
            for qubit_no in range(QUBITS_PER_MONEY):
                q = host.get_data_qubit(customer, wait=10)
                if bank_basis[serial_to_be_checked][qubit_no] == 1:
                    q.H()

                measurement = q.measure()
                if measurement != bank_bits[serial_to_be_checked][qubit_no]:
                    print('Money is invalid!')
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
            print('Customer received money')

        def verify_money():
            print('Customer is verifying the money')
            serial_of_money_to_be_used = randint(0, NO_OF_SERIALS - 1)
            host.send_classical(banker, serial_of_money_to_be_used)

            for qubit_no in range(QUBITS_PER_MONEY):
                host.send_qubit(banker, money_qubits[serial_of_money_to_be_used][qubit_no])

        print('Customer is awaiting serial number and qubits that represent the money')
        receive_money()
        print('Customer is getting his money verified')
        verify_money()


    def sniffing_quantum(sender, receiver, qubit):
        """
        Function to set what the relay node does to the qubit in transmission.

        Args:
            sender (Host) : Sender of the qubit
            receiver (Host) : Receiver of the qubit
            qubit (Qubit): Qubit in transmission
        """

        # Eavesdropper measures some of the qubits.
        if sender == 'Bank' and random() <= 0.25:
            print('Eavesdropper measured qubit from %s to %s' % (sender, receiver))
            qubit.measure(non_destructive=True)


    def main():
        # Initialize a network
        network = Network.get_instance()
        backend = ProjectQBackend()
        nodes = ['Bank', 'Customer', 'Eve']
        network.delay = 0.1
        network.start(nodes, backend)

        host_bank = Host('Bank', backend)
        host_bank.add_connection('Eve')
        host_bank.start()

        host_eve = Host('Eve', backend)
        host_eve.add_connection('Bank')
        host_eve.add_connection('Customer')
        host_eve.start()

        host_customer = Host('Customer', backend)
        host_customer.add_connection('Eve')
        host_customer.start()

        network.add_host(host_bank)
        network.add_host(host_eve)
        network.add_host(host_customer)

        host_eve.quantum_relay_sniffing = True
        host_eve.set_quantum_relay_sniffing_function(sniffing_quantum)

        print('Starting transfer')
        t1 = host_bank.run_protocol(banker_protocol, (host_customer.host_id,))
        t2 = host_customer.run_protocol(customer_protocol, (host_bank.host_id,))

        t1.join()
        t2.join()

        network.stop(True)


    if __name__ == '__main__':
        main()
