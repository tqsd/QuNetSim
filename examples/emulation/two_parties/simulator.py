from qunetsim import Simulator
from qunetsim.backends import EQSNBackend
from qunetsim.components import Network


def main():
    host_ids = ["Alice", "Bob"]
    networking_card_paths = ["/dev/tty0", "/dev/tty1"]

    connections = {"Alice": "Bob",
                   "Bob": "Alice"}

    # define the backend used as simulator
    backend = EQSNBackend()

    # Create the simulator class
    Simulator(host_ids, connections, networking_card_paths, backend)


if __name__ == "__main__":
    main()
