import cqc.pythonLib as cqc
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network as SimulaNetwork
from functools import partial as fp
from objects.qubit import Qubit
import numpy as np
import threading

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
        self.lock.acquire_read()
        ret = self.dict[key]
        self.lock.release_read()
        return ret

class CQCBackend(object):
    """
    The Simulaqron CQC backend
    """

    class Hosts(SafeDict):
        # There only should be one instance of Hosts
        __instance = None

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

    # Simulaqron comes with an own network simulator
    # has to be kept in sync with QuNetSim network
    backend_network = None
    backend_network_lock = RWLock()

    def __init__(self):
        self._hosts = CQCBackend.Hosts.get_instance()
        self._cqc_connections = CQCBackend.CQCConnections.get_instance()


    def start(self, **kwargs):
        """
        Starts Backends which have to run in an own thread or process before they
        can be used.

        Args:
            nodes(List): A list of hosts in the network.
        """
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
        CQCBackend.backend_network_lock.acquire_write()
        CQCBackend.backend_network.stop()
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

        Reurns:
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
        cqc_from_host.sendQubit(qubit._qubit, cqc_to_host.name)
        qubit.set_new_qubit(cqc_to_host.recvQubit())
        qubit.set_new_host(self._hosts.get_from_dict(to_host_id))

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
        cqc_host_a = self._cqc_connections.get_from_dict(host_a_id)
        cqc_host_b = self._cqc_connections.get_from_dict(host_b_id)
        host_a = self._hosts.get_from_dict(host_a_id)
        q = cqc_host_a.createEPR(cqc_host_b.name)
        return Qubit(host_a, qubit=q, q_id=q_id, blocked=block)

    def receive_epr(self, host_id, q_id=None, block=False):
        cqc_host = self._cqc_connections.get_from_dict(host_id)
        host = self._hosts.get_from_dict(host_id)
        q = cqc_host.recvEPR()
        return Qubit(host, qubit=q, q_id=q_id, blocked=block)

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

    def rx(self, qubit, phi):
        """
        Perform a rotation pauli x gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        qubit.qubit.rot_X(steps)

    def ry(self, qubit, phi):
        """
        Perform a rotation pauli y gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
        # convert to cqc unit
        steps = phi * 256.0 / (2.0 * np.pi)
        qubit.qubit.rot_Y(steps)

    def rz(self, qubit, phi):
        """
        Perform a rotation pauli z gate with an angle of phi.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
            phi (float): Amount of rotation in Rad.
        """
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
        """
        Perform a measurement on a qubit.

        Args:
            qubit (Qubit): Qubit which should be measured.

        Returns:
            The value which has been measured.
        """
        return qubit.qubit.measure()

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        qubit.qubit.release()
