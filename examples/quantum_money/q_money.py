from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit, Logger
from random import randint

#Logger(file='./trial4.log')
Logger.DISABLED = False

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

    print("Banker is preparing and distributing qubits")
    preparation_and_distribution()
    print("Banker is awaiting verification from customer")
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

    print('Customer is awaiting serial number')
    receive_money()
    print('Customer is verifying')
    verify_money()


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

    print('Starting transfer')
    t1 = host_alice.run_protocol(banker_protocol, (host_eve.host_id,))
    t2 = host_eve.run_protocol(customer_protocol, (host_alice.host_id,))

    t1.join()
    t2.join()

    network.stop(True)


if __name__ == '__main__':
    main()
