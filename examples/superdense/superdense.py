from cqc.pythonLib import CQCConnection, qubit
import sys
import time

sys.path.append("../..")
from components.host import Host
from components.network import Network


def main():
    network = Network.get_instance()
    network.set_delay(0.2)
    #network.set_drop_rate(0.3)
    network.start()

    with CQCConnection('Alice') as Alice, CQCConnection('Bob') as Bob, \
            CQCConnection('Eve') as Eve, CQCConnection('Dean') as Dean:

        alice = Host('00000000', Alice)
        alice.add_connection('00000001')
        alice.start()

        bob = Host('00000001', Bob)
        bob.add_connection('00000011')
        bob.start()

        eve = Host('00000011', Eve)
        eve.add_connection('00000111')
        eve.start()

        dean = Host('00000111', Dean)
        dean.start()

        network.add_host(alice)
        network.add_host(bob)
        network.add_host(eve)
        network.add_host(dean)

        time.sleep(2)


        alice.send_superdense('00000001', '00',True)
        # alice.send_epr('00000001')
        # alice.send_epr('00000001')
        # alice.send_epr('00000001')
        # alice.send_superdense('00000001', '11')
        # alice.send_superdense('00000001', '10')
        alice.send_superdense('00000011', '00', True)
        alice.send_classical('00000011', 'hello')
        # alice.send_epr('00000111')
        # alice.send_epr('00000011')
        # alice.send_epr('00000001')
        # alice.send_superdense('00000011', '10')
        # alice.send_superdense('00000011', '01')
        # alice.send_epr('00000111')
        # alice.send_epr('00000011')
        # alice.send_epr('00000001')
        # alice.send_superdense('00000111', '00')
        # alice.send_superdense('00000111', '11')
        # alice.send_superdense('00000111', '10')

        nodes = [alice, bob, eve, dean]

        start_time = time.time()
        while time.time() - start_time < 60:
            pass

        for h in nodes:
            h.stop()

        network.stop()


main()
