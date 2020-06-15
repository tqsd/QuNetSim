import time

from qunetsim.backends.safe_dict import SafeDict
from qunetsim.objects.qubit import Qubit
from queue import Queue

try:
    import projectq
except ImportError:
    raise RuntimeError(
        'To use ProjectQ as a backend, you need to first install the Python package '
        '\'projectq\' (e.g. run \'pip install projectq\'.')


class ProjectQBackend(object):
    def __init__(self):
        self._hosts = ProjectQBackend.Hosts.get_instance()
        self._entaglement_pairs = ProjectQBackend.EntanglementPairs.get_instance()
        self.engine = projectq.MainEngine()
        self.measuring = False

    def __del__(self):
        self.engine.flush(deallocate_qubits=True)

    class EntanglementPairs(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if ProjectQBackend.EntanglementPairs.__instance is not None:
                return ProjectQBackend.EntanglementPairs.__instance
            else:
                return ProjectQBackend.EntanglementPairs()

        def __init__(self):
            if ProjectQBackend.EntanglementPairs.__instance is not None:
                raise Exception("Call get instance to get this class!")
            ProjectQBackend.EntanglementPairs.__instance = self
            SafeDict.__init__(self)

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if ProjectQBackend.Hosts.__instance is not None:
                return ProjectQBackend.Hosts.__instance
            else:
                return ProjectQBackend.Hosts()

        def __init__(self):
            if ProjectQBackend.Hosts.__instance is not None:
                raise Exception("Call get instance to get this class!")
            ProjectQBackend.Hosts.__instance = self
            SafeDict.__init__(self)

    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.
        """
        pass

    def stop(self):
        """
        Stops Backends which are running in an own thread or process.
        """
        self.engine.flush(deallocate_qubits=True)
        pass

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
            host_id (String): Id of the host to whom the qubit belongs.

        Returns:
            Qubit of backend type.
        """
        return self.engine.allocate_qubit()

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        """
        qubit.host = self._hosts.get_from_dict(to_host_id)

    def create_EPR(self, host_a_id, host_b_id, q_id=None, block=False):
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
        q1 = self.create_qubit(host_a_id)
        q2 = self.create_qubit(host_b_id)

        projectq.ops.H | q1
        projectq.ops.CNOT | (q1, q2)

        host_a = self._hosts.get_from_dict(host_a_id)
        host_b = self._hosts.get_from_dict(host_b_id)
        qubit_b = Qubit(host_b, qubit=q2, q_id=q_id, blocked=block)
        qubit = Qubit(host_a, qubit=q1, q_id=q_id, blocked=block)
        self.store_ent_pair(host_a.host_id, host_b.host_id, qubit_b)
        return qubit

    def store_ent_pair(self, host_a, host_b, qubit):
        key = host_a + ':' + host_b
        ent_queue = self._entaglement_pairs.get_from_dict(key)

        if ent_queue is not None:
            ent_queue.put(qubit)
        else:
            ent_queue = Queue()
            ent_queue.put(qubit)
        self._entaglement_pairs.add_to_dict(key, ent_queue)

    def receive_epr(self, host_id, sender_id, q_id=None, block=False):
        """
        Called after create EPR in the receiver, to receive the other EPR pair.

        Args:
            host_id (String): ID of the first host who gets the EPR state.
            sender_id (String): ID of the sender of the EPR pair.
            q_id (String): Optional id which both qubits should have.
            block (bool): Determines if the created pair should be blocked or not.
        Returns:
            Returns an EPR qubit with the other Host.
        """
        key = sender_id + ':' + host_id
        ent_queue = self._entaglement_pairs.get_from_dict(key)
        if ent_queue is None:
            raise Exception("Internal Error!")
        qubit = ent_queue.get()
        if q_id is not None and q_id != qubit.id:
            raise ValueError("Qid doesn't match id!")
        return qubit

    ##########################
    #   Gate definitions    #
    #########################

    def I(self, qubit):
        """
        Perform Identity gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        pass

    def X(self, qubit):
        """
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.X | qubit.qubit

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.Y | qubit.qubit

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.Z | qubit.qubit

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.H | qubit.qubit

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.T | qubit.qubit

    def K(self, qubit):
        """
        Perform K gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        projectq.ops.H | qubit.qubit
        projectq.ops.S | qubit.qubit
        projectq.ops.H | qubit.qubit
        projectq.ops.Z | qubit.qubit

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        projectq.ops.Rx(phi) | qubit.qubit

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        projectq.ops.Ry(phi) | qubit.qubit

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        projectq.ops.Rz(phi) | qubit.qubit

    def cnot(self, control, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            control (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        projectq.ops.CNOT | (control.qubit, target.qubit)

    def cphase(self, control, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            control (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        projectq.ops.CZ | (control.qubit, target.qubit)

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
        while self.measuring:
            time.sleep(0.1)
            pass

        self.measuring = True
        projectq.ops.Measure | qubit.qubit
        m = int(qubit.qubit)

        if not non_destructive:
            self.release(qubit)
            self.engine.flush()
        self.measuring = False
        return m

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        while self.measuring:
            time.sleep(0.1)
            pass
        self.measuring = True
        projectq.ops.Measure | qubit.qubit
        self.engine.flush()
        self.measuring = False
