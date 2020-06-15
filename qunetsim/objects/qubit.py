import uuid
import numpy as np


class Qubit(object):
    """
    A Qubit object. It is a wrapper class of qubits of different
    backends, which adds additional information needed for QuNetSim.
    """

    DATA_QUBIT = "data"
    EPR_QUBIT = "EPR"
    GHZ_QUBIT = "GHZ"

    def __init__(self, host, qubit=None, q_id=None, blocked=False):
        self._blocked = blocked
        self._host = host
        if q_id is not None:
            self._id = str(q_id)
        else:
            self._id = str(uuid.uuid4())
        if qubit is not None:
            self._qubit = qubit
        else:
            self._qubit = self._host.backend.create_qubit(self._host.host_id)

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

    @property
    def qubit(self):
        """
        Return the physical qubit.

        Returns:
            (backend.qubit) qubit: Return the physical qubit.
        """
        return self._qubit

    @qubit.setter
    def qubit(self, qubit):
        """
        Set the physical qubit.

        Args:
            qubit: the physical qubit.
        """
        self._qubit = qubit

    @host.setter
    def host(self, host):
        """
        Set the host of this qubit.

        Args:
            host (str): The host ID for the qubit.
        """
        self._host = host

    @id.setter
    def id(self, new_id):
        """
        Give the qubit a new id.

        Args:
            new_id (str): new id of the qubit.
        """
        self._id = str(new_id)

    @blocked.setter
    def blocked(self, state):
        """
        Set the blocked state of the qubit.

        Args:
            state (bool): True for blocked, False if not.
        """
        self._blocked = state

    def send_to(self, receiver_id):
        """
        Sends the Qubit to another host.

        Args:
            receiver_id (String): ID of Host the qubit should be send to.
        """
        self._host.backend.send_qubit_to(self, self._host.host_id, receiver_id)

    def release(self):
        """
        Releases a qubit from the system.
        """
        self._host.backend.release(self)

    def I(self):
        """
        Perform Identity operation on the qubit.
        """
        self._host.backend.I(self)

    def X(self):
        """
        Perform pauli x gate on qubit.
        """
        self._host.backend.X(self)

    def Y(self):
        """
        Perform pauli y gate on qubit.
        """
        self._host.backend.Y(self)

    def Z(self):
        """
        Perform pauli z gate on qubit.
        """
        self._host.backend.Z(self)

    def T(self):
        """
        Perform a T gate on the qubit.
        """
        self._host.backend.T(self)

    def K(self):
        """
        Perform a K gate on the qubit.
        """
        self._host.backend.K(self)

    def H(self):
        """
        Perform a Hadamard gate on the qubit.
        """
        self._host.backend.H(self)

    def rx(self, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        self._host.backend.rx(self, phi)

    def ry(self, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        self._host.backend.ry(self, phi)

    def rz(self, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            phi (float): Rotation in rad
        """
        self._host.backend.rz(self, phi)

    def cnot(self, target):
        """
        Applies a controlled x gate to the target qubit.

        Args:
            target (Qubit): Qubit on which the cnot gate should be applied.
        """
        self._host.backend.cnot(self, target)

    def cphase(self, target):
        """
        Applies a controlled z gate to the target qubit.

        Args:
            target (Qubit): Qubit on which the cphase gate should be applied.
        """
        self._host.backend.cphase(self, target)

    def custom_gate(self, gate):
        """
        Applies a custom 2x2 unitary on the qubit.

        Args:
            gate (Numpy ndarray): A unitary 2x2 matrix
        """

        if not isinstance(gate, np.ndarray):
            raise (InputError("Only Numpy matrices are allowed"))
        if not is_unitary(gate):
            raise (InputError("Custom gates must be unitary operations"))
        if gate.shape != (2, 2):
            raise (InputError("Custom gates must be 2x2 matrices"))

        self._host.backend.custom_gate(self, gate)

    def custom_controlled_gate(self, target, gate):
        """
        Applies a custom 2x2 unitary on the qubit.

        Args:
            target (Qubit): Qubit on which the controlled gate should be applied.
            gate (Numpy ndarray): A unitary 2x2 matrix
        """

        if not isinstance(gate, np.ndarray):
            raise (InputError("Only Numpy arrays are allowed"))
        if not is_unitary(gate):
            raise (InputError("Custom gates must be unitary operations"))
        if gate.shape != (2, 2):
            raise (InputError("Custom controlled gates must be 2x2 matrices"))

        self._host.backend.custom_controlled_gate(self, target, gate)

    def custom_two_qubit_gate(self, other_qubit, gate):
        """
        Applies a custom 2 qubit gate.

        Args:
            other_qubit (Qubit): The second qubit.
            gate (Numpy ndarray): The gate

        """
        if not isinstance(gate, np.ndarray):
            raise (InputError("Only Numpy matrices are allowed"))
        if not is_unitary(gate):
            raise (InputError("Custom gates must be unitary operations"))
        if gate.shape != (4, 4):
            raise (InputError("Custom controlled gates must be 2x2 matrices"))

        self._host.backend.custom_two_qubit_gate(self, other_qubit, gate)

    def measure(self, non_destructive=False):
        """
        Measures the state of a qubit.

        Args:
            non_destructive (bool): Determines if the qubit should stay in the
                                    system or be eliminated.

        Returns:
            measured_value (int): 0 or 1, dependent on measurement outcome.
        """
        return self._host.backend.measure(self, non_destructive)


def is_unitary(m):
    return np.allclose(np.eye(m.shape[0]), m.conj().T.dot(m))


class InputError(Exception):
    """
    Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
