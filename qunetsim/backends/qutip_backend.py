from qunetsim.backends.safe_dict import SafeDict
from qunetsim.backends.rw_lock import RWLock
from qunetsim.objects.qubit import Qubit
from queue import Queue
from itertools import zip_longest
import warnings
import numpy as np
import uuid
import random

try:
    import qutip
    from qutip.cy.spmath import zcsr_kron
    from qutip.qip.operations import cnot, snot, gate_expand_1toN, gate_expand_2toN,\
                                    rx, ry, rz, csign
except ImportError:
    raise RuntimeError(
        'To use QuTip as a backend, you need to first install the Python package '
        '\'qutip\' (e.g. run \'pip install qutip\'.')


class QuTipBackend(object):
    """
    Definition of how a backend has to look and behave like.
    """
    class QubitCollection(object):

        def __init__(self, name):
            # initialize as a qubit in state |0>
            self._rwlock = RWLock()
            self.N = 1
            self._qubit_names = [name]
            self.data = qutip.qutip.fock_dm(2, 0)

        def add_qubit(self, qubit):
            """
            Calculates the tensor product using the implementation
            of QuTip.
            Modified vesion of qutip tensor function,
            See http://qutip.org/docs/4.0.2/modules/qutip/tensor.html
            """
            self._lock()
            self.data = qutip.tensor(self.data, qubit.data)
            self.N = self.N + qubit.N
            self._qubit_names = self._qubit_names + qubit._qubit_names
            self._unlock()

        def apply_single_gate(self, gate, qubit_name):
            if not isinstance(gate, qutip.Qobj):
                raise TypeError("Gate has to be of type Qobject.")
            self._lock()
            target = self._qubit_names.index(qubit_name)
            gate = qutip.gate_expand_1toN(gate, self.N, target)
            self.data = gate * self.data * gate.dag()
            self._unlock()

        def apply_double_gate(self, gate, control_name, target_name):
            if not isinstance(gate, qutip.Qobj):
                raise TypeError("Gate has to be of type Qobject.")
            self._lock()
            control = self._qubit_names.index(control_name)
            target = self._qubit_names.index(target_name)
            gate = qutip.gate_expand_2toN(gate, self.N, control, target)
            self.data = gate * self.data * gate.dag()
            self._unlock()

        def measure(self, qubit_name, non_destructive):
            res = None
            M_0 = qutip.fock(2, 0).proj()
            M_1 = qutip.fock(2, 1).proj()
            self._lock()
            target = self._qubit_names.index(qubit_name)
            if self.N > 1:
                M_0 = qutip.gate_expand_1toN(M_0, self.N, target)
                M_1 = qutip.gate_expand_1toN(M_1, self.N, target)
            pr_0 = qutip.expect(M_0, self.data)
            pr_1 = qutip.expect(M_1, self.data)
            outcome = int(np.random.choice([0, 1], 1, p=[pr_0, pr_1]))
            if outcome == 0:
                self.data = M_0 * self.data * M_0.dag() / pr_0
                res = 0
            else:
                # M_1 = qutip.gate_expand_1toN(M_1, self.N, target)
                self.data = M_1 * self.data * M_1.dag() / pr_1
                res = 1
            if non_destructive is False:
                i_list = [x for x in range(self.N)]
                i_list.remove(target)
                self._qubit_names.remove(qubit_name)
                self.N = self.N - 1
                if len(i_list) > 0:
                    self.data = self.data.ptrace(i_list)
                else:
                    self.data = qutip.Qobj()
            self._unlock()
            return res

        def give_density_matrix(self, qubit_name):
            ret = None
            self._lock()
            if qubit_name in self._qubit_names:
                index = self._qubit_names.index(qubit_name)
                ret = self.data.ptrace([index])
            self._unlock()
            return ret

        def _lock(self):
            self._rwlock.acquire_write()

        def _unlock(self):
            self._rwlock.release_write()

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if QuTipBackend.Hosts.__instance is not None:
                return QuTipBackend.Hosts.__instance
            else:
                return QuTipBackend.Hosts()

        def __init__(self):
            if QuTipBackend.Hosts.__instance is not None:
                raise Exception("Call get instance to get this class!")
            QuTipBackend.Hosts.__instance = self
            SafeDict.__init__(self)

    class EntanglementIDs(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

        @staticmethod
        def get_instance():
            if QuTipBackend.EntanglementIDs.__instance is not None:
                return QuTipBackend.EntanglementIDs.__instance
            else:
                return QuTipBackend.EntanglementIDs()

        def __init__(self):
            if QuTipBackend.EntanglementIDs.__instance is not None:
                raise Exception("Call get instance to get this class!")
            QuTipBackend.EntanglementIDs.__instance = self
            SafeDict.__init__(self)

    def __init__(self):
        self._hosts = QuTipBackend.Hosts.get_instance()
        self._entaglement_qubits = QuTipBackend.EntanglementIDs.get_instance()

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

        Reurns:
            Qubit of backend type.
        """
        name = str(uuid.uuid4())
        return (QuTipBackend.QubitCollection(name), name)

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
        name1 = str(uuid.uuid4())
        name2 = str(uuid.uuid4())
        host_a = self._hosts.get_from_dict(host_a_id)
        host_b = self._hosts.get_from_dict(host_b_id)
        qubit1 = (QuTipBackend.QubitCollection(name1), name1)
        qubit2 = (QuTipBackend.QubitCollection(name2), name2)
        qubit1[0].apply_single_gate(snot(), qubit1[1])
        qubit1[0].add_qubit(qubit2[0])
        qubit2 = (qubit1[0], name2)
        qubit1[0].apply_double_gate(cnot(), qubit1[1], qubit2[1])
        q1 = Qubit(host_a, qubit=qubit1, q_id=q_id, blocked=block)
        q2 = Qubit(host_b, qubit=qubit2, q_id=q1.id, blocked=block)
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
        return

    def X(self, qubit):
        """
        Perform pauli X gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        gate = rx(np.pi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def Y(self, qubit):
        """
        Perform pauli Y gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        gate = ry(np.pi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def Z(self, qubit):
        """
        Perform pauli Z gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        gate = rz(np.pi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        gate = snot()
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def T(self, qubit):
        """
        Perform T gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        gate = np.array([[1, 0], [0, np.e**(1j*np.pi/4)]])
        self.custom_gate(qubit, gate)

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        gate = rx(phi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        gate = ry(phi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        gate = rz(phi)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def cnot(self, qubit, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cnot.
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        gate = cnot()
        qubit_collection, c_name = qubit.qubit
        qubit_collection2, t_name = target.qubit
        if qubit_collection != qubit_collection2:
            qubit_collection.add_qubit(qubit_collection2)
            target.qubit = (qubit_collection, t_name)
        qubit_collection.apply_double_gate(gate, c_name, t_name)

    def cphase(self, qubit, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            qubit (Qubit): Qubit to control cphase.
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        gate = csign()
        qubit_collection, c_name = qubit.qubit
        qubit_collection2, t_name = target.qubit
        if qubit_collection != qubit_collection2:
            qubit_collection.add_qubit(qubit_collection2)
            target.qubit = (qubit_collection, t_name)
        qubit_collection.apply_double_gate(gate, c_name, t_name)

    def custom_gate(self, qubit, gate):
        """
        Applies a custom gate to the qubit.

        Args:
            qubit(Qubit): Qubit to which the gate is applied.
            gate(np.ndarray): 2x2 array of the gate.
        """
        gate = qutip.Qobj(gate)
        qubit_collection, name = qubit.qubit
        qubit_collection.apply_single_gate(gate, name)

    def custom_controlled_gate(self, qubit, target, gate):
        """
        Applies a custom gate to the target qubit, controlled by the qubit.

        Args:
            qubit(Qubit): Qubit to control the gate.
            target(Qubit): Qubit on which the gate is applied.
            gate(nd.array): 2x2 array for the gate applied to target.
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
        raise (EnvironmentError("Not implemeted for this backend!"))

    def custom_two_qubit_gate(self, qubit1, qubit2, gate):
        """
        Applies a custom two qubit gate to qubit1 \\otimes qubit2.

        Args:
            qubit1(Qubit): First qubit of the gate.
            qubit2(Qubit): Second qubit of the gate.
            gate(np.ndarray): 4x4 array for the gate applied.
        """
        gate = qutip.Qobj(gate)
        qubit_collection, c_name = qubit1.qubit
        qubit_collection2, t_name = qubit2.qubit
        if qubit_collection != qubit_collection2:
            qubit_collection.add_qubit(qubit_collection2)
            qubit2.qubit = (qubit_collection, t_name)
        qubit_collection.apply_double_gate(gate, c_name, t_name)

    def density_operator(self, qubit):
        """
        Returns the density operator of this qubit. If the qubit is entangled,
        the density operator will be in a mixed state.

        Args:
            qubit (Qubit): Qubit of the density operator.

        Returns:
            np.ndarray: The density operator of the qubit.
        """
        qubit_collection, q_name = qubit.qubit
        return qubit_collection.give_density_matrix(q_name)

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
        q, name = qubit.qubit
        return q.measure(name, non_destructive)

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))
