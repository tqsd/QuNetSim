import cqc.pythonLib as cqc
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network as SimulaNetwork

from qunetsim.backends.rw_lock import RWLock
from qunetsim.backends.safe_dict import SafeDict
from qunetsim.objects.qubit import Qubit


class CQCBackend(object):
    """
    The SimulaQron CQC backend
    """

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if CQCBackend.Hosts.__instance is not None:
                return CQCBackend.Hosts.__instance
            else:
                return CQCBackend.Hosts()

        def __init__(self):
            if CQCBackend.Hosts.__instance is not None:
                raise Exception("Call get instance to get this class!")
            CQCBackend.Hosts.__instance = self
            SafeDict.__init__(self)

    class CQCConnections(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if CQCBackend.CQCConnections.__instance is not None:
                return CQCBackend.CQCConnections.__instance
            else:
                return CQCBackend.CQCConnections()

        def __init__(self):
            if CQCBackend.CQCConnections.__instance is not None:
                raise Exception("Call get instance to get this class!")
            CQCBackend.CQCConnections.__instance = self
            SafeDict.__init__(self)

    # SimulaQron comes with an own network simulator
    # has to be kept in sync with QuNetSim network
    backend_network = None
    backend_network_lock = RWLock()

    def __init__(self):
        self._hosts = CQCBackend.Hosts.get_instance()
        self._cqc_connections = CQCBackend.CQCConnections.get_instance()
        self._stopped = False

    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.

        Args:
            nodes(List): A list of hosts in the network.
        """
        print('Starting SimulaQron Network...')
        nodes = kwargs['nodes']
        CQCBackend.backend_network_lock.acquire_write()
        simulaqron_settings.default_settings()
        CQCBackend.backend_network = SimulaNetwork(nodes=nodes, force=True)
        CQCBackend.backend_network.start()
        CQCBackend.backend_network_lock.release_write()

    def stop(self):
        """
        Stops Backends which are running in an own thread or process.
        """
        if not self._stopped:
            CQCBackend.backend_network_lock.acquire_write()
            CQCBackend.backend_network.stop()
            self._stopped = True
            CQCBackend.backend_network_lock.release_write()

    def add_host(self, host):
        """
        Adds a host to the backend.

        Args:
            host (Host): New Host which should be added.
        """
        connection = cqc.CQCConnection(host.host_id)
        self._cqc_connections.add_to_dict(host.host_id, connection)
        self._hosts.add_to_dict(host.host_id, host)

    def create_qubit(self, host_id):
        """
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Returns:
            Qubit of backend type.
        """
        return cqc.qubit(self._cqc_connections.get_from_dict(host_id))

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        """
        cqc_from_host = self._cqc_connections.get_from_dict(from_host_id)
        cqc_to_host = self._cqc_connections.get_from_dict(to_host_id)
        cqc_from_host.sendQubit(qubit.qubit, cqc_to_host.name)
        qubit.qubit = cqc_to_host.recvQubit()
        qubit.host = self._hosts.get_from_dict(to_host_id)

    def create_EPR(self, host_id, q_id=None, block=False):
        """
        Creates an EPR pair for two qubits and returns one of the qubits.

        Args:
            host_a_id (String): ID of the first host who gets the EPR state.
            host_b_id (String): ID of the second host who gets the EPR state.
            q_id (String): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Returns a qubit. The qubit belongs to host a. To get the second
            qubit of host b, the receive_epr function has to be called.
        """
        host = self._hosts.get_from_dict(host_id)
        cqc_host = self._cqc_connections.get_from_dict(host_id)
        q1 = cqc.qubit(cqc_host)
        q2 = cqc.qubit(cqc_host)
        q1.H()
        q1.cnot(q2)
        q1 = Qubit(host, qubit=q1, q_id=id, blocked=block)
        q2 = Qubit(host, qubit=q2, q_id=id, blocked=block)
        return q1, q2

    def flush(self, host_id):
        """
        CQC specific function.
        """
        self._cqc_connections.get_from_dict(host_id).flush()

    ##########################
    #   Gate definitions    #
    #########################

    def I(self, qubit):
        """
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        qubit.qubit.I()

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
        qubit.qubit.Y()

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
        qubit.qubit.T()

    def K(self, qubit):
        """
        Perform K gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        qubit.qubit.K()

    def rx(self, qubit, steps):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            steps (int): Amount of rotation in Rad.
        """
        # convert to cqc unit
        if steps < 0:
            steps = 256 + steps
        qubit.qubit.rot_X(steps)

    def ry(self, qubit, steps):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            steps (int): Amount of rotation in Rad.
        """
        # convert to cqc unit
        # steps = phi * 256.0 / (2.0 * np.pi)
        if steps < 0:
            steps = 256 + steps
        qubit.qubit.rot_Y(steps)

    def rz(self, qubit, steps):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        # convert to cqc unit
        # steps = phi * 256.0 / (2.0 * np.pi)
        if steps < 0:
            steps = 256 + steps
        qubit.qubit.rot_Z(steps)

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
        qubit.qubit.cphase(target.qubit)

    def custom_gate(self, qubit, gate):
        """
        Applies a custom gate to the qubit.

        Args:
            qubit(Qubit): Qubit to which the gate is applied.
            gate(np.ndarray): 2x2 array of the gate.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_controlled_gate(self, qubit, target, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit(Qubit): Qubit to control the gate.
            target(Qubit): Qubit on which the gate is applied.
            gate(nd.array): 2x2 array for the gate applied to target.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_two_qubit_gate(self, qubit1, qubit2, gate):
        """
        Applies a custom two qubit gate to qubit1 \\otimes qubit2.

        Args:
            qubit1(Qubit): First qubit of the gate.
            qubit2(Qubit): Second qubit of the gate.
            gate(np.ndarray): 4x4 array for the gate applied.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def custom_controlled_two_qubit_gate(self, qubit, target_1, target_2, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit (Qubit): Qubit to control the gate.
            target_1 (Qubit): Qubit on which the gate is applied.
            target_2 (Qubit): Qubit on which the gate is applied.
            gate (nd.array): 4x4 array for the gate applied to target.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

    def density_operator(self, qubit):
        """
        Returns the density operator of this qubit. If the qubit is entangled,
        the density operator will be in a mixed state.

        Args:
            qubit (Qubit): Qubit of the density operator.

        Returns:
            np.ndarray: The density operator of the qubit.
        """
        raise (EnvironmentError("Not implemented for this backend!"))

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
        return qubit.qubit.measure(inplace=non_destructive)

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        qubit.qubit.release()
