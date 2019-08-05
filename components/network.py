# Network singleton
class Network:
    __instance = None

    @staticmethod
    def get_instance():
        if Network.__instance is None:
            Network()
        return Network.__instance

    def __init__(self):
        if Network.__instance is None:
            self.ARP = {}
            Network.__instance = self
        else:
            raise Exception('this is a singleton class')

    def add_host(self, host):
        self.ARP[host.host_id] = host

    def get_host(self, host_id):
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id]

    def get_host_name(self, host_id):
        if host_id not in self.ARP:
            return None
        return self.ARP[host_id].cqc.name

    def send(self, packet, host_id):
        self.ARP[host_id].rec_packet(packet)
