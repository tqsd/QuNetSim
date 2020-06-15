from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger

Logger.DISABLED = False

# In this example, we send a data qubit from
# Alice to Dean who sits 2 hops away from Alice
# in the network.

def main():
    network = Network.get_instance()
    nodes = ["Alice", "Bob", "Eve", "Dean"]
    network.start(nodes)
    network.delay = 0.1

    host_alice = Host('Alice')
    host_alice.add_connection('Bob')
    host_alice.start()

    host_bob = Host('Bob')
    host_bob.add_connection('Alice')
    host_bob.add_connection('Eve')
    host_bob.start()

    host_eve = Host('Eve')
    host_eve.add_connection('Bob')
    host_eve.add_connection('Dean')
    host_eve.start()

    host_dean = Host('Dean')
    host_dean.add_connection('Eve')
    host_dean.start()

    network.add_host(host_alice)
    network.add_host(host_bob)
    network.add_host(host_eve)
    network.add_host(host_dean)

    # Create a qubit owned by Alice
    q = Qubit(host_alice)
    # Put the qubit in the excited state
    q.X()
    # Send the qubit and await an ACK from Dean
    q_id = host_alice.send_qubit('Dean', q, no_ack=True)

    # Get the qubit on Dean's side from Alice
    q_rec = host_dean.get_data_qubit('Alice', q_id)

    # Ensure the qubit arrived and then measure and print the results.
    if q_rec is not None:
        m = q_rec.measure()
        print("Results of the measurements for q_id are ", str(m))
    else:
        print('q_rec is none')

    network.stop(True)
    exit()


if __name__ == '__main__':
    main()
