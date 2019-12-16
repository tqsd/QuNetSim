


def QuantumStorage(object):
    '''
    An object which stores qubits.
    '''


    def __init__(self):
        pass

    def add_qubit_from_host(self, qubit, from_host_id):
        '''
        Adds a qubit which has been received from a host.

        Args:
            qubit (Qubit): qubit which should be stored.
            from_host (int): Id of the Host from whom the qubit has
                             been received.
        '''
        pass

    def give_qubit_from_host(self, from_host):
        '''
        Returns next qubit which has been received from a host.

        Args:
            from_host (Host): Host from who the qubit has been received.
        '''
        pass
