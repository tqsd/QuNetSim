from qunetsim.components.simulator import Simulator
from qunetsim.backends import QuTipBackend
from qunetsim.components import Network
from qunetsim.objects import Logger

Logger.DISABLED = False

def main():
    host_ids = ["Alice"]
    networking_card_paths = ["/dev/ttyUSB0"]


    connections = {}

    # define the backend used as simulator
    backend = QuTipBackend()

    # Create the simulator class
    Simulator(host_ids, connections, networking_card_paths, backend)


if __name__ == "__main__":
    main()
