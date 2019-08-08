from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network
from components.logger import Logger


def main():
    network = Network.get_instance()
    logger = Logger.get_instance()
    print('')

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob:
        host_alice = Host('00000001', Alice)
        host_alice.add_connection('00000000')
        host_alice.start()
        network.add_host(host_alice)

        host_bob = Host('00000000', Bob)
        host_bob.add_connection('00000001')
        host_bob.start()
        network.add_host(host_bob)

        host_sender = network.get_host('00000001')
        host_receiver = network.get_host('00000000')

        q = qubit(Alice)
        q.X()

        logger.log(network.get_host_name('00000001') + ' sends epr')
        host_sender.send_teleport('00000000', q)

        start_time = time.time()
        while time.time() - start_time < 10:
            pass

        logger.log('stopping hosts')
        host_sender.stop()
        host_receiver.stop()


main()
