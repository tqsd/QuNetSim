import cqc.pythonLib as cqc
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network as SimulaNetwork
from backends.backend import Backend
from functools import partial as fp
from objects.qubit import Qubit


class CQCBackend(object):
    '''
    The Simulaqron CQC backend
    '''

    def __init__(self):
        self.cqc_connections = {}
        self.hosts = {}
        # Simulaqron comes with an own network simulator
        self._backend_network = None

    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.

        Args:
            nodes(List): A list of hosts in the network.
        """
        nodes = kwargs['nodes']
        simulaqron_settings.default_settings()
        self._backend_network = SimulaNetwork(nodes=nodes, force=True)
        self._backend_network.start()

    def stop(self):
        """
        Stops Backends which are running in an own thread or process.
        """
        self._backend_network.stop()

    def add_host(self, host):
        '''
        Adds a host to the backend.

        Args:
            host (Host): New Host which should be added.
        '''
        connection = cqc.CQCConnection(host.host_id)
        self.cqc_connections[host.host_id] = connection
        self.hosts[host.host_id] = host

    def create_qubit(self, host_id):
        '''
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Reurns:
            Qubit of backend type.
        '''
        return cqc.qubit(self.cqc_connections[host_id])

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        '''
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        '''
        cqc_from_host = self.cqc_connections[from_host_id]
        cqc_to_host = self.cqc_connections[to_host_id]
        cqc_from_host.sendQubit(qubit._qubit, cqc_to_host.name)
        qubit.set_new_qubit(cqc_to_host.recvQubit())
        qubit.set_new_host(self.hosts[to_host_id])
        self.hosts[to_host_id].add_data_qubit(from_host_id, qubit)

    def create_EPR_states(self, host_a_id, host_b_id, id=None, block=False):
        '''
        Creates an EPR pair for two qubits and returns them.

        Args:
            host_a_id (String): ID of the first host who gets the EPR state.
            host_b_id (String): ID of the second host who gets the EPR state.
            id (String): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Tuple of a qubit and another tuple, which is a function, the qubit
            id and the blocked state.
            The qubit belongs to host a, the function has to be called by host b
            to get the second part of the EPR state.
        '''
        cqc_host_a = self.cqc_connections[host_a_id]
        cqc_host_b = self.cqc_connections[host_b_id]
        q = cqc_host_a.createEPR(cqc_host_b.name)
        q = Qubit(self.hosts[host_a_id], qubit=q, q_id=id, blocked=block)
        id = q.id

        def receive_epr(cqc_host, host, id, blocked):
            q = cqc_host.recvEPR()
            q = Qubit(host, qubit=q, q_id=id, blocked=blocked)
            return q

        func = fp(receive_epr, cqc_host_b, self.hosts[host_b_id], id, block)
        return q, (func, id, block)

    def flush(self, host_id):
        '''
        CQC specific function.
        '''
        self.cqc_connections[host_id].flush()

    ##########################
    #   Gate definitions    #
    #########################

    def I(self, qubit):
        '''
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.I()

    def X(self, qubit):
        '''
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.X()

    def Y(self, qubit):
        '''
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.Y()

    def Z(self, qubit):
        '''
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.Z()

    def H(self, qubit):
        '''
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.H()

    def T(self, qubit):
        '''
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        '''
        qubit.qubit.T()

    def rx(self, qubit, phi):
        '''
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        qubit.qubit.rot_X(steps)

    def ry(self, qubit, phi):
        '''
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        qubit.qubit.rot_Y(steps)

    def rz(self, phi):
        '''
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        '''
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
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

    def measure(self, qubit):
        '''
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.

        Returns:
            The value which has been measured.
        '''
        return qubit.qubit.measure()

    def release(self, qubit):
        '''
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        '''
        qubit.qubit.release()
