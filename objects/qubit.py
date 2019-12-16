import cqc.pythonLib as cqc
import numpy as np
import uuid


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
        return self._qubit

    def set_new_qubit(self, qubit):
        self._qubit = qubit

    def set_new_host(self, host):
        self._host = host

    def set_new_id(self, new_id):
        """
        Give the qubit a new id.

        Args:
            new_id (str): new id of the qubit.
        """
        self._id = new_id

    def set_blocked_state(self, state):
        """
        Set the bockes state of the qubit.

        Args:
            state (bool): True for blocked, False if not.
        """
        self._blocked = state

    def send_to(self, receiver_id):
        """
        Sends the Qubit to another host.

        Args:
            receiver (String): ID of Host the qubit should be send to.
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

    def measure(self):
        """
        Measures the state of a qubit.

        Returns:
            measured_value (int): 0 or 1, dependent on measurement outcome.
        """
        return self._host.backend.measure(self)
