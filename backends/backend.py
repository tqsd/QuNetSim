

def Backend(object):
    '''
    Definition of how a backend has to look and behave like.
    '''

    def __init__(self):
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def add_host(self, host):
        '''
        Adds a host to the backend.

        Args:
            host (Host): New Host which should be added.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def send_qubit_to(self, qubit, to_host):
        '''
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            to_host (Host): New host of the qubit.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def create_EPR_states(self, host_a, host_b):
        '''
        Creates an EPR pair for two qubits and returns them.

        Args:
            host_a (Host): The first host who gets the EPR state.
            host_b (Host): The second host who gets the EPR state.

        Returns:
            Tuple of qubits, first qubit is EPR of host a, second of host b.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    ##########################
    #   Gate definitions    #
    #########################

    def I(self, qubit):
        '''
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def X(self, qubit):
        '''
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def Y(self, qubit):
        '''
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def Z(self, qubit):
        '''
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def H(self, qubit):
        '''
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def T(self, qubit):
        '''
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def rx(self, qubit, phi):
        '''
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def ry(self, qubit, phi):
        '''
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def rz(self, phi):
        '''
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def measure(self, qubit):
        '''
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.

        Returns:
            The value which has been measured.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))
