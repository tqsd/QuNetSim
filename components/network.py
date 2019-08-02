# Network singleton
class Network:
    ARP = {}
    instance = None

    class __Network:
        def __init__(self):
            pass

    def __init__(self):
        if not Network.instance:
            Network.instance = Network.__Network()

    def add_host(self, host):
        self.ARP[host.host_id] = host

    def get_host(self, host_id):
        if not self.ARP[host_id]:
            return None
        return self.ARP[host_id]

    def send(self, packet, host_id):
        self.ARP[host_id].rec_packet(packet)
