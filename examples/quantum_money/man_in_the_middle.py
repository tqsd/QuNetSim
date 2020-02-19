from components.host import Host
from components.network import Network
from components.logger import Logger
from objects.qubit import Qubit
from random import randint, random
from backends.projectq_backend import ProjectQBackend

Logger.DISABLED = True

WAIT_TIME = 10
QUBITS_PER_MONEY = 10
NO_OF_SERIALS = 1


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
                cheat_alert = True

        if not cheat_alert:
            print('MONEY IS VALID')
        else:
            print('MONEY IS INVALID!')

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
        serial_to_be_used = randint(0, NO_OF_SERIALS - 1)
        host.send_classical(banker, serial_to_be_used)

        for qubit_no in range(QUBITS_PER_MONEY):
            host.send_qubit(banker, money_qubits[serial_to_be_used][qubit_no], await_ack=False)

        # Remove unused qubits
        unused_serials = list(range(NO_OF_SERIALS))
        del unused_serials[serial_to_be_used]
        for unused_serial in unused_serials:
            for q in money_qubits[unused_serial]:
                q.release()

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
    if sender == 'Customer' and random() <= 0.50:
        print('Eavesdropper applied X qubit from %s to %s' % (sender, receiver))
        qubit.X()
    elif sender == 'Customer':
        print('Eavesdropper applied H qubit from %s to %s' % (sender, receiver))
        qubit.H()


def main():
    # Initialize a network
    network = Network.get_instance()
    # backend = CQCBackend()
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
    host_customer.delay = 0.3
    host_customer.start()

    network.add_host(host_bank)
    network.add_host(host_eve)
    network.add_host(host_customer)

    host_eve.quantum_relay_sniffing = True
    host_eve.set_quantum_relay_sniffing_function(sniffing_quantum)

    print('Starting transfer')

    t = host_customer.run_protocol(customer_protocol, (host_bank.host_id,))
    host_bank.run_protocol(banker_protocol, (host_customer.host_id,), blocking=True)
    t.join()

    network.stop(True)


if __name__ == '__main__':
    main()
