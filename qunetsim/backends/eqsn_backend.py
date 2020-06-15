from eqsn import EQSN
import uuid
from qunetsim.objects.qubit import Qubit
import threading
from queue import Queue


# From O'Reilly Python Cookbook by David Ascher, Alex Martelli
# with some smaller adaptions
class RWLock:
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._num_reader = 0
        self._num_writer = 0
        self._readerList = []
        self._writerList = []

    def acquire_read(self):
        self._read_ready.acquire()
        try:
            while self._num_writer > 0:
                self._read_ready.wait()
            self._num_reader += 1
        finally:
            self._readerList.append(threading.get_ident())
            self._read_ready.release()

    def release_read(self):
        self._read_ready.acquire()
        try:
            self._num_reader -= 1
            if not self._num_reader:
                self._read_ready.notifyAll()
        finally:
            self._readerList.remove(threading.get_ident())
            self._read_ready.release()

    def acquire_write(self):
        self._read_ready.acquire()
        self._num_writer += 1
        self._writerList.append(threading.get_ident())
        while self._num_reader > 0:
            self._read_ready.wait()

    def release_write(self):
        self._num_writer -= 1
        self._writerList.remove(threading.get_ident())
        self._read_ready.notifyAll()
        self._read_ready.release()


class SafeDict(object):
    def __init__(self):
        self.lock = RWLock()
        self.dict = {}

    def __str__(self):
        self.lock.acquire_read()
        ret = str(self.dict)
        self.lock.release_read()
        return ret

    def add_to_dict(self, key, value):
        self.lock.acquire_write()
        self.dict[key] = value
        self.lock.release_write()

    def get_from_dict(self, key):
        ret = None
        self.lock.acquire_read()
        if key in self.dict:
            ret = self.dict[key]
        self.lock.release_read()
        return ret


class EQSNBackend(object):
    """
    Definition of how a backend has to look and behave like.
    """

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if EQSNBackend.Hosts.__instance is not None:
                return EQSNBackend.Hosts.__instance
            else:
                return EQSNBackend.Hosts()

        def __init__(self):
            if EQSNBackend.Hosts.__instance is not None:
                raise Exception("Call get instance to get this class!")
            EQSNBackend.Hosts.__instance = self
            SafeDict.__init__(self)

    class EntanglementIDs(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if EQSNBackend.EntanglementIDs.__instance is not None:
                return EQSNBackend.EntanglementIDs.__instance
            else:
                return EQSNBackend.EntanglementIDs()

        def __init__(self):
            if EQSNBackend.EntanglementIDs.__instance is not None:
                raise Exception("Call get instance to get this class!")
            EQSNBackend.EntanglementIDs.__instance = self
            SafeDict.__init__(self)

    def __init__(self):
        self._hosts = EQSNBackend.Hosts.get_instance()
        # keys are from : to, where from is the host calling create EPR
        self._entaglement_qubits = EQSNBackend.EntanglementIDs.get_instance()
        self.eqsn = EQSN.get_instance()

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
        self.eqsn.stop_all()

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
        id = str(uuid.uuid4())
        self.eqsn.new_qubit(id)
        return id

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        """
        new_host = self._hosts.get_from_dict(to_host_id)
        qubit.host = new_host

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
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        host_a = self._hosts.get_from_dict(host_a_id)
        host_b = self._hosts.get_from_dict(host_b_id)
        self.eqsn.new_qubit(uid1)
        self.eqsn.new_qubit(uid2)
        self.eqsn.H_gate(uid1)
        self.eqsn.cnot_gate(uid2, uid1)
        q1 = Qubit(host_a, qubit=uid1, q_id=q_id, blocked=block)
        q2 = Qubit(host_b, qubit=uid2, q_id=q1.id, blocked=block)
        self.store_ent_pair(host_a.host_id, host_b.host_id, q2)
        return q1

    def store_ent_pair(self, host_a, host_b, qubit):
        key = host_a + ':' + host_b
        ent_queue = self._entaglement_qubits.get_from_dict(key)

        if ent_queue is not None:
            ent_queue.put(qubit)
        else:
            ent_queue = Queue()
            ent_queue.put(qubit)
        self._entaglement_qubits.add_to_dict(key, ent_queue)

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
        ent_queue = self._entaglement_qubits.get_from_dict(key)
        if ent_queue is None:
            raise Exception("Internal Error!")
        q = ent_queue.get()
        self._entaglement_qubits.add_to_dict(key, ent_queue)
        if q_id is not None and q_id != q.id:
            raise ValueError("Qid doesent match id!")
        return q

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
        self.eqsn.X_gate(qubit.qubit)

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.Y_gate(qubit.qubit)

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.Z_gate(qubit.qubit)

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.H_gate(qubit.qubit)

    def K(self, qubit):
        """
        Perform K gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.K_gate(qubit.qubit)

    def S(self, qubit):
        """
        Perform S gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.S_gate(qubit.qubit)

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        self.eqsn.T_gate(qubit.qubit)

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        self.eqsn.RX_gate(qubit.qubit, phi)

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        self.eqsn.RY_gate(qubit.qubit, phi)

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of roation in Rad.
        """
        self.eqsn.RZ_gate(qubit.qubit, phi)

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        self.eqsn.cnot_gate(target.qubit, qubit.qubit)

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        self.eqsn.cphase_gate(target.qubit, qubit.qubit)

    def custom_gate(self, qubit, gate):
        """
        Applies a custom gate to the qubit.

        Args:
            qubit(Qubit): Qubit to which the gate is applied.
            gate(np.ndarray): 2x2 array of the gate.
        """
        self.eqsn.custom_gate(qubit.qubit, gate)

    def custom_controlled_gate(self, qubit, target, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit(Qubit): Qubit to control the gate.
            target(Qubit): Qubit on which the gate is applied.
            gate(nd.array): 2x2 array for the gate applied to target.
        """
        self.eqsn.custom_controlled_gate(target.qubit, qubit.qubit, gate)

    def custom_two_qubit_gate(self, qubit1, qubit2, gate):
        """
        Applies a custom two qubit gate to qubit1 \\otimes qubit2.

        Args:
            qubit1(Qubit): First qubit of the gate.
            qubit2(Qubit): Second qubit of the gate.
            gate(np.ndarray): 4x4 array for the gate applied.
        """
        self.eqsn.custom_two_qubit_gate(qubit1.qubit, qubit2.qubit, gate)

    def measure(self, qubit, non_destructive):
        """
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.
            non_destructive (bool): If the qubit should be destroyed after measuring.

        Returns:
            The value which has been measured.
        """
        return self.eqsn.measure(qubit.qubit, non_destructive)

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        self.eqsn.measure(qubit.qubit)
