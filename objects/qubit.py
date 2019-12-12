from cqc.pythonLib import qubit as cqc.qubit
import numpy as np

def cqc_qubit_to_qubit(cqc_qubit, q_id, blocked=False):
    cqc_qubit.q_id = q_id
    cqc_qubit.blocked = blocked
    cqc_qubit.__class__ = Qubit
    return cqc_qubit


class Qubit(object):
    """
    A Qubit object. It is a wrapper class of qubits of different
    backends, which adds additional information needed for QuNetSim.
    """


    def __init__(self, host, qubit=None, q_id=None, blocked=False):
        self._blocked = blocked
        self._host = host
        if q_id is not None:
            self._id = q_id
        else:
            self._id = str(uuid.uuid4())
        if qubit is not None:
            self._qubit = qubit
        else:
            self._qubit = cqc.qubit(host.cqc)

    @property
    def host(self):
        """
        Give the host of who the qubit belongs to.

        Returns:
            Host of the qubit.
        """
        return self._host

    @property
    def id(self):
        """
        Give the ID of the qubit.

        Returns:
            Id of the qubit.
        """
        return self._id

    @property
    def blocked(self):
        """
        Give the block state of the qubit.

        Returns:
            If the qubit is blocked or not.
        """
        return self._blocked

    def set_new_id(self, new_id):
        """
        Give the qubit a new id.

        Args:
            new_id (int): new id of the qubit.
        """
        self._id = new_id

    def set_blocked_state(self, state):
        """
        Set the bockes state of the qubit.

        Args:
            state (bool): True for blocked, False if not.
        """
        self._blocked = state

    def release(self):
        """
        Releases a qubit from the system.
        """
        self._qubit.release()

    def I(self):
        """
        Perform Identity operation on the qubit.
        """
        self._qubit.X()

    def X(self):
        """
        Perform pauli x gate on qubit.
        """
        self._qubit.Y()

    def Y(self):
        """
        Perform pauli y gate on qubit.
        """
        self._qubit.Y()

    def Z(self):
        """
        Perform pauli z gate on qubit.
        """
        self._qubit.Z()

    def T(self):
        """
        Perform a T gate on the qubit.
        """
        self._qubit.T()

    def H(self):
        """
        Perform a Hadamard gate on the qubit.
        """
        self._qubit.H()

    def K(self):
        """
        Perform a K gate on the qubit.
        """
        self._qubit.K()

    def rx(self, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        self._qubit.rot_X(steps)

    def ry(self, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        self._qubit.rot_Y(steps)

    def rz(self, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        self._qubit.rot_Z(steps)

    def cnot(self, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            target (qubit): Qubit on which the cnot gate should be applied.
        """
        self._qubit.cnot(target._qubit)

    def cphase(self, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            target (qubit): Qubit on which the cphase gate should be applied.
        """
        self._qubit.cphase(target._qubit)

    def measure(self):
        """
        Measures the state of a qubit.

        Returns:
            measured_value (int): 0 or 1, dependent on measurement outcome.
        """
        return self._qubit.measure()
