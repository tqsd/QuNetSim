from qunetsim.backends.rw_lock import RWLock
from qunetsim.objects.qubit import Qubit
import uuid
from copy import deepcopy as dp
import enum
try:
    import serial
except ImportError:
    raise RuntimeError(" To use the Emulated Backend you need to install "
                       "pyserial!")


class Commands(enum.Enum):
    IDLE = 0
    APPLY_GATE_SINGLE_GATE = 1
    APPLY_DOUBLE_GATE = 2
    MEASURE = 3
    NEW_QUBIT = 4
    SEND_QUBIT = 5
    CREATE_ENTANGLED_PAIR = 6


class SingleGates(enum.Enum):
    Idenitity = 0
    X = 1
    Y = 2
    Z = 3
    H = 4
    S = 5
    T = 6
    RX = 7
    RY = 8
    RZ = 9


class DoubleGates(enum.Enum):
    CNOT = 0
    CPHASE = 1


idle_frame = {}
single_gate_frame = [["qubit_id", None, 12 * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, 8]]
double_gate_frame = [["first_qubit_id", None, 12 * 8],
                     ["second_qubit_id", None, 12 * 8],
                     ["gate", None, 8],
                     ["gate_parameter", None, 8]]
measure_frame = [["qubit_id", None, 12 * 8],
                 ["options", None, 8]]
new_qubit_frame = [["qubit_id", None, 12 * 8]]
send_qubit_frame = [["qubit_id", None, 12 * 8],
                    ["host_to_send_to", None, 64]]
create_epr_frame = [["first_qubit_id", None, 12 * 8],
                    ["second_qubit_id", None, 12 * 8]]

Command_to_frame = [idle_frame, single_gate_frame, double_gate_frame,
                    measure_frame, new_qubit_frame, send_qubit_frame,
                    create_epr_frame]

command_basis_frame = [['command', None, 8]]


def create_binary_frame(dataframe, byteorder='big'):
    binary_output = b''

    def query_frame(frame, binary_string):
        for entry in dataframe:
            print(entry[1])
            if isinstance(entry[1], int):
                if entry[2] % 8 == 0:
                    binary_string = binary_string + entry[1].to_bytes(int(entry[2]/8), byteorder=byteorder, signed=False)
                else:
                    pass
            elif isinstance(entry[1], bytearray):
                if len(entry[1]) != int(entry[2]/8):
                    raise ValueError("Size of the binary string does not match the frame size!")
                binary_string = binary_string + entry[1]
            elif isinstance(entry[1], list):
                binary_string = binary_string + query_frame(entry[1], binary_string)
            else:
                raise ValueError("Unknown Type!")
        return binary_string

    return query_frame(dataframe, binary_output)

def create_frame(command, qubit_id=None, first_qubit_id=None, second_qubit_id=None, gate=None, gate_parameter=None,
                 options=None, host_to_send_to=None):
    values = {}
    if command not in set(item.value for item in Commands):
        raise ValueError("Command does not exist!")
    values["command"] = command
    if qubit_id is not None:
        values['qubit_id'] = qubit_id
    if first_qubit_id is not None:
        values['first_qubit_id'] = first_qubit_id
    if second_qubit_id is not None:
        values["second_qubit_id"] = second_qubit_id
    if gate is not None:
        if gate not in set(item.value for item in SingleGates):
            if gate not in set(item.value for item in DoubleGates):
                raise ValueError("This gate does not exist!")
        values["gate"] = gate
    if gate_parameter is not None:
        values["gate_parameter"] = gate_parameter
    if options is not None:
        values["options"] = options
    if host_to_send_to is not None:
        values["host_to_send_to"] = host_to_send_to
    frame = dp(command_basis_frame)
    frame = frame + dp(Command_to_frame[command])

    for entry in frame:
        entry[1] = values[entry[0]]

    return frame



class EmulationBackend(object):
    """
    Backend which connects to a Quantum Networking Card.
    """

    class NetworkingCard(object):
        # There only should be one instance of NetworkingCard
        __instance = None

        @staticmethod
        def get_instance():
            if EmulationBackend.NetworkingCard.__instance is not None:
                return EmulationBackend.NetworkingCard.__instance
            else:
                return EmulationBackend.NetworkingCard()

        def __init__(self):
            if EmulationBackend.NetworkingCard.__instance is not None:
                raise Exception("Call get instance to get the object.")
            EmulationBackend.NetworkingCard.__instance = self
            self._lock = RWLock()

        def send_bytestring(self, bytestring):
            self._lock.acquire_write()
            # # TODO: send data over connection
            self._lock.release_write()

    def __init__(self):
        self.networking_card = EmulationBackend.NetworkingCard.get_instance()

    def _send_to_networking_card(self, frame):
        binary_string = create_binary_frame(frame)
        self.networking_card.send_bytestring(binary_string)

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
        raise EnvironmentError("This is only an interface, not \
                        an actual implementation!")

    def create_qubit(self, host_id):
        """
        Creates a new Qubit of the type of the backend.

        Args:
            host_id (String): Id of the host to whom the qubit belongs.

        Reurns:
            Qubit of backend type.
        """
        id = uuid.uuid4().bytes
        frame = create_frame(Commands.NEW_QUBIT.value, qubit_id=id)
        self._send_to_networking_card(frame)
        return id

    def send_qubit_to(self, qubit, from_host_id, to_host_id):
        """
        Sends a qubit to a new host.

        Args:
            qubit (Qubit): Qubit to be send.
            from_host_id (String): From the starting host.
            to_host_id (String): New host of the qubit.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

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
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

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
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

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
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def H(self, qubit):
        """
        Perform Hadamard gate on a qubit.

        Args:
            qubit (Qubit): Qubit on which gate should be applied to.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

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
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

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
        Returns the density operator of this qubit. If the qubit is entangled,
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
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))

    def release(self, qubit):
        """
        Releases the qubit.

        Args:
            qubit (Qubit): The qubit which should be released.
        """
        raise (EnvironmentError("This is only an interface, not \
                        an actual implementation!"))
