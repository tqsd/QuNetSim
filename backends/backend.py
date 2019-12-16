

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
        raise EnvironmentError("This is only an interface, not \
                        an actual implementation!")

    def create_qubit(self, host_id):
        '''
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Reurns:
            Qubit of backend type.
        '''
        raise EnvironmentError("This is only an interface, not \
                        an actual implementation!")

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        '''
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def create_EPR_states(self, host_a_id, host_b_id, id=None, block=False):
        '''
        Creates an EPR pair for two qubits and returns them.

        Args:
            host_a_id (String): ID of the first host who gets the EPR state.
            host_b_id (String): ID of the second host who gets the EPR state.
            id (String): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Tuple of a qubit and a function. The qubit belongs to host a,
            the function has to be called by host b to get the second part
            of the EPR state.
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

    def release(self, qubit):
        '''
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        '''
        raise(EnvironmentError("This is only an interface, not \
                        an actual implementation!"))
