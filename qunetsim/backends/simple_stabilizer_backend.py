from qunetsim.backends import SafeDict
from numpy import random


class SimpleStabilizerQubit:
    def __init__(self, q_id):
        self.entangled_pairs = []
        self.state = 0
        self._ops = []
        self._is_entangled = False
        self._q_id = q_id

    @property
    def q_id(self):
        return self._q_id

    def X(self):
        if len(self._ops) == 0 or self._ops[-1] != 'X':
            self._ops.append('X')
            self.state = 1
        else:
            self._ops.pop()

    def Z(self):
        if len(self._ops) == 0 or self._ops[-1] != 'Z':
            self._ops.append('Z')
        else:
            self._ops.pop()

    def H(self):
        if self._is_entangled:
            return

        if len(self._ops) == 0 or self._ops[-1] != 'H':
            self._ops.append('H')
        else:
            self._ops.pop()

    def cnot(self, target):
        if self._is_entangled or len(self._ops) == 0:
            return

        if self._ops[-1] == 'X':
            target.X()
        elif self._ops[-1] == 'H':
            self._is_entangled = True
            target._is_entangled = True
            target.entangled_pairs.append(self)
            self.entangled_pairs.append(target)
            self._ops.pop()

    def measure(self):
        if len(self._ops) == 0:
            if self._is_entangled:
                return self.state
            return 0
        elif len(self._ops) == 1:
            op = self._ops.pop()
            if self._is_entangled:
                if op == 'X':
                    self.entangled_pairs[0].state = 1
                    return 0
                elif op == 'Z':
                    self.entangled_pairs[0].state = 0
                    return 1
            else:
                if op == 'X':
                    return self.state
                if op == 'H':
                    return random.choice([0, 1])
                return 0
        elif len(self._ops) == 2:
            if self._is_entangled:
                self.entangled_pairs[0].state = 1
                return 1
            return 0
        else:
            return 0


class SimpleStabilizerBackend:
    """
    Definition of how a backend has to look and behave like.
    """

    def __init__(self):
        self._hosts = SafeDict()
        self._num_qubits = 0
        self._qubits = {}

    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.
        """
        raise EnvironmentError("This is only an interface, not \
                        an actual implementation!")

    def stop(self):
        """
        Stops Backends which are running in an own thread or process.
        """
        raise EnvironmentError("This is only an interface, not \
                        an actual implementation!")

    def add_host(self, host):
        """
        Adds a host to the backend.

        Args:
            host (Host): New Host which should be added.
        """
        self._hosts.add_to_dict(host.host_id, host)

    def create_qubit(self, host_id):
        """
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (str): Id of the host to whom the qubit belongs.

        Returns:
            Qubit of backend type.
        """
        q = SimpleStabilizerQubit(self._num_qubits)
        self._qubits[self._num_qubits] = q
        self._num_qubits += 1
        return q

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (str): From the starting host.
            to_host_id (str): New host of the qubit.
        """
        qubit.host = self._hosts.get_from_dict(to_host_id)

    def create_EPR(self, host_a_id, host_b_id, q_id=None, block=False):
        """
        Creates an EPR pair for two qubits and returns one of the qubits.

        Args:
            host_a_id (str): ID of the first host who gets the EPR state.
            host_b_id (str): ID of the second host who gets the EPR state.
            q_id (str): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Returns a qubit. The qubit belongs to host a. To get the second
            qubit of host b, the receive_epr function has to be called.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def receive_epr(self, host_id, sender_id, q_id=None, block=False):
        """
        Called after create EPR in the receiver, to receive the other EPR pair.

        Args:
            host_id (str): ID of the first host who gets the EPR state.
            sender_id (str): ID of the sender of the EPR pair.
            q_id (str): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Returns an EPR qubit with the other Host.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    ##########################
    #   Gate definitions    #
    #########################

    def I(self, qubit):
        """
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def X(self, qubit):
        """
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        qubit.qubit.X()

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        qubit.qubit.Z()

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        qubit.qubit.H()

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def rz(self, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        qubit.qubit.cnot(target.qubit)

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def custom_gate(self, qubit, gate):
        """
        Applies a custom gate to the qubit.

        Args:
            qubit(Qubit): Qubit to which the gate is applied.
            gate(np.ndarray): 2x2 array of the gate.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def custom_controlled_gate(self, qubit, target, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit(Qubit): Qubit to control the gate.
            target(Qubit): Qubit on which the gate is applied.
            gate(nd.array): 2x2 array for the gate applied to target.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def custom_controlled_two_qubit_gate(self, qubit, target_1, target_2, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit (Qubit): Qubit to control the gate.
            target_1 (Qubit): Qubit on which the gate is applied.
            target_2 (Qubit): Qubit on which the gate is applied.
            gate (nd.array): 4x4 array for the gate applied to target.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def custom_two_qubit_gate(self, qubit1, qubit2, gate):
        """
        Applies a custom two qubit gate to qubit1 \\otimes qubit2.

        Args:
            qubit1(Qubit): First qubit of the gate.
            qubit2(Qubit): Second qubit of the gate.
            gate(np.ndarray): 4x4 array for the gate applied.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def density_operator(self, qubit):
        """
        Returns the density operator of this qubit. I the qubit is entangled,
        the density operator will be in a mixed state.

        Args:
            qubit (Qubit): Qubit of the density operator.

        Returns:
            np.ndarray: The density operator of the qubit.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def measure(self, qubit, non_destructive):
        """
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.
            non_destructive (bool): Determines if the Qubit should stay in the
                                    system or be eliminated.

        Returns:
            The value which has been measured.
        """
        if qubit.qubit.q_id not in self._qubits:
            raise Exception('Qubit does not exist')

        m = qubit.qubit.measure()
        if not non_destructive:
            del self._qubits[qubit.qubit.q_id]

        return m

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))
