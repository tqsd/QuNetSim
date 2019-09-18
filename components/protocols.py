from cqc.pythonLib import qubit
import uuid

# DATA TYPES
from components.logger import Logger
from components.network import Network

network = Network.get_instance()

CLASSICAL = '00'
QUANTUM = '11'
SIGNAL = '10'

# QUBIT TYPES
EPR = 0
DATA = 1

# SIGNALS
ACK = '1111'
NACK = '0000'

# PROTOCOL IDs
REC_EPR = '00000000'
SEND_EPR = '00000001'
REC_TELEPORT = '00000011'
SEND_TELEPORT = '00000100'
REC_SUPERDENSE = '00000101'
SEND_UDP = '00000111'
TERMINATE_UDP = '00001000'
SEND_ACK = '00001001'
REC_ACK = '00001010'
SEND_CLASSICAL = '00001011'
REC_CLASSICAL = '00001100'
SEND_SUPERDENSE = '00001101'
RELAY = '00001111'
REC_TELEPORT_EPR = '00010001'
SEND_TELEPORT_EPR = '0001010'

MAX_WAIT = 30
WAIT_ITER = 1


def process(packet):
    """
    Decodes the packet and processes the packet according to the protocol in the packet header.

    Args:
        packet (dict): Packet to be processed.

    Returns:
        Returns what protocol function returns.

    """
    sender, receiver, protocol, payload, payload_type, rec_sequence_num = _parse_message(packet)
    if protocol == SEND_TELEPORT:
        return _send_teleport(sender, receiver, payload, rec_sequence_num)
    elif protocol == REC_TELEPORT:
        return _rec_teleport(sender, receiver, payload)
    elif protocol == SEND_CLASSICAL:
        return _send_classical(sender, receiver, payload, rec_sequence_num)
    elif protocol == REC_CLASSICAL:
        return _rec_classical(sender, receiver, payload, rec_sequence_num)
    elif protocol == REC_EPR:
        return _rec_epr(sender, receiver, payload)
    elif protocol == SEND_EPR:
        return _send_epr(sender, receiver, payload)
    elif protocol == SEND_SUPERDENSE:
        return _send_superdense(sender, receiver, payload, rec_sequence_num)
    elif protocol == REC_SUPERDENSE:
        return _rec_superdense(sender, receiver, payload, rec_sequence_num)
    elif protocol == RELAY:
        return _relay_message(receiver, packet)
    else:
        Logger.get_instance().error('protocol not defined')


def encode(sender, receiver, protocol, payload=None, payload_type='', sequence_num=-1):
    """
    Encodes the data with the sender, receiver, protocol, payload type and sequence number and forms the packet
    with data and the header.

    Args:
        sender(string): ID of the sender
        receiver(string): ID of the receiver
        protocol(string): ID of the protocol of which the packet should be processed.
        payload : The message that is intended to send with the packet. Type of payload depends on the protocol.
        payload_type(string): Type of the payload.
        sequence_num(int): Sequence number of the packet.
    Returns:
         dict: Encoded packet

    """
    packet = {
        'sender': sender,
        'receiver': receiver,
        'protocol': protocol,
        'payload_type': payload_type,
        'payload': payload,
        'sequence_number': sequence_num
    }
    return packet


def _parse_message(message):
    """
    Parses the packet to its components : sender, receiver, protocol, payload, payload_type, sequence number.

    Args:
        message (dict): Packet to be parsed

    Returns:
         Host: Sender of the packet,
         Host: receiver of the packet,
         string: the protocol which the packet should be processed,
         dict: payload,
         string: type of the payload,
         int: sequence number of the packet
    """
    sender = message['sender']
    receiver = message['receiver']
    protocol = message['protocol']
    payload_type = message['payload_type']
    payload = message['payload']

    if 'sequence_number' in message:
        rec_sequence_num = message['sequence_number']
        return sender, receiver, protocol, payload, payload_type, rec_sequence_num
    else:
        return sender, receiver, protocol, payload, payload_type, None


def _relay_message(receiver, packet):
    """
    Sends the message to be relayed to the next node in the network and modifies the header.

    Args:
        receiver (Host): Receiver of the packet
        packet (dict): Packet to be relayed

    """
    packet['TTL'] -= 1
    packet['sender'] = receiver
    packet['receiver'] = packet['payload']['receiver']
    network.send(packet)


def _send_classical(sender, receiver, message, rec_sequence_num):
    """
    Sends a classical message to another host.

    Args:
        sender (Host): Sender of the message
        receiver (Host): Receiver of the message
        message (string): Message to be sent
        rec_sequence_num (int): Sequence number of the packet

    """
    host_sender = network.get_host(sender)
    packet = encode(host_sender.host_id, receiver, REC_CLASSICAL, {'message': message}, CLASSICAL, rec_sequence_num)
    host_receiver = network.get_host(receiver)

    if not (host_receiver or host_sender):
        # TODO: create a meaningful exception
        raise Exception

    network.send(packet)


def _rec_classical(sender, receiver, payload, rec_sequence_num):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an
    ACK message to receiver.

    Args:
        sender (Host): Sender of the message
        receiver (Host): Receiver of the message
        payload (dict): Packet to be parsed
        rec_sequence_num: Sequence number of the received packet

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """

    # Assume the payload is the classical message
    _send_ack(sender, receiver)
    return {'message': payload['message'], 'sequence_number': rec_sequence_num}


def _send_teleport(sender, receiver, payload, rec_sequence_num):
    """
    Does the measurements for teleportation of a qubit and sends the measurement results to another host.

    Args:
        sender (Host): Sender of the teleported qubit
        receiver (Host): Receiver of the teleported qubit
        payload (dict): A dictionary consisting of information about the teleported qubit , such as the type of the
                        qubit (EPR or DATA) , if it is EPR the initial sender of the qubit.
        rec_sequence_num (int): Sequence number of the packet to be sent

    """

    if 'node' in payload:
        node = payload['node']
    else:
        node = sender

    if 'type' in payload:
        q_type = payload['type']
    else:
        q_type = DATA

    if 'type' in payload:
        type = payload['type']

    q = payload['q']

    host_sender = network.get_host(sender)
    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        q_id = str(uuid.uuid4())
        packet = encode(sender, receiver, REC_EPR, payload={'q_id': q_id},
                        payload_type=SIGNAL)
        network.send(packet)

    epr_teleport = host_sender.get_epr(receiver)

    while epr_teleport is None:
        epr_teleport = host_sender.get_epr(receiver)

    q.cnot(epr_teleport['q'])
    q.H()

    m1 = q.measure()
    m2 = epr_teleport['q'].measure()

    data = {'measurements': [m1, m2], 'q_id': epr_teleport['q_id'], 'type': q_type, 'node': node}
    packet = encode(sender, receiver, REC_TELEPORT, data, CLASSICAL, rec_sequence_num)
    network.send(packet)


def _rec_teleport(sender, receiver, payload):
    """
    Receives a classical message and applies the required operations to EPR pair entangled with the sender to
    retrieve the teleported qubit.

    Args:
        sender (Host): Sender of the teleported qubit
        receiver (Host): Receiver of the teleported qubit
        payload (dict): A dictionary consisting of information about the measurements necessary to complete the
                        teleportation and the initial receiver of the qubit if qubit is an EPR qubit.
    """
    host_receiver = network.get_host(receiver)
    q_id = payload['q_id']

    q = host_receiver.get_epr(sender, q_id)

    while q is None:
        q = host_receiver.get_epr(sender, q_id)

    a = payload['measurements'][0]
    b = payload['measurements'][1]
    epr_host = payload['node']

    # Apply corrections
    if a == 1:
        q.Z()
    if b == 1:
        q.X()

    if payload['type'] == EPR:
        host_receiver.add_epr(epr_host, q, q_id)

    elif payload['type'] == DATA:
        host_receiver.add_data_qubit(epr_host, q, q_id)

    _send_ack(sender, receiver)


def _send_epr(sender, receiver, payload=None):
    """
    Sends an EPR to another host in the network.

    Args:
        sender (Host): Sender of the EPR
        receiver (Host): Receiver of the EPR
        payload (dict): A dictionary consisting of qubit ID of the EPR pair

    """

    if payload is not None:
        payload = {'q_id': payload}

    packet = encode(sender, receiver, REC_EPR, payload=payload, payload_type=SIGNAL)
    network.send(packet)


def _rec_epr(sender, receiver, payload):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an ACK message to
    receiver.

    Args:
        sender: ID of sender
        receiver: ID of receiver
        payload (dict): Packet to be parsed

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """

    host_receiver = network.get_host(receiver)
    q = host_receiver.cqc.recvEPR()
    if payload is None:
        host_receiver.add_epr(sender, q)
    else:
        host_receiver.add_epr(sender, q, q_id=payload['q_id'])
    return _send_ack(sender, receiver)


def _send_ack(sender, receiver):
    return


def _send_superdense(sender, receiver, payload, rec_sequence_num):
    """
    Encodes and sends a qubit to send a superdense message.

    Args:
        sender (Host): Sender of the superdense message
        receiver (Host): Receiver of the superdense qubit
        payload (string): The message to be sent
        rec_sequence_num (int): Sequence number of the packet
    """
    host_sender = network.get_host(sender)
    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        q_id = str(uuid.uuid4())
        packet = encode(sender, receiver, REC_EPR, payload={'q_id': q_id},
                        payload_type=SIGNAL)
        network.send(packet)

    q_superdense = host_sender.get_epr(receiver)
    while q_superdense is None:
        q_superdense = host_sender.get_epr(receiver)

    if q_superdense is None:
        print('q is none')

    _encode_superdense(payload, q_superdense['q'])
    packet = encode(sender, receiver, REC_SUPERDENSE, [q_superdense], QUANTUM, rec_sequence_num)
    network.send(packet)


def _rec_superdense(sender, receiver, payload, rec_sequence_num):
    """
    Receives a superdense qubit and decodes it.

    Args:
        sender (Host): Sender of the superdense message
        receiver (Host): Receiver of the superdense qubit
        payload (dict): The message that contains the qubit ID
        rec_sequence_num (int): Sequence number of the packet

    Returns:
        dict : A dictionary consisting of decoded superdense message and sequence number
    """
    host_receiver = network.get_host(receiver)

    q1 = host_receiver.get_data_qubit(sender, payload[0]['q_id'])
    while q1 is None:
        q1 = host_receiver.get_data_qubit(sender, payload[0]['q_id'])

    q2 = host_receiver.get_epr(sender, payload[0]['q_id'])
    while q2 is None:
        q2 = host_receiver.get_epr(sender, payload[0]['q_id'])

    return {'message': _decode_superdense(q1, q2), 'sequence_number': rec_sequence_num}


def _add_checksum(sender, qubits, size=2):
    i = 0
    check_qubits = []
    while i < len(qubits):
        check = qubit(sender)
        j = 0
        while j < size:
            qubits[i + j].cnot(check)
            j += 1

        check_qubits.append(check)
        i += size
    return check_qubits


def _encode_superdense(message, q):
    """
    Encode qubit q with the 2 bit message.

    Args:

        message: the message to encode
        qubit: the qubit to encode the message

    """
    if message == '00':
        # do nothing (i.e. perform identity)
        pass
    elif message == '01':
        q.X()
    elif message == '10':
        q.Z()
    elif message == '11':
        q.X()
        q.Z()
    else:
        raise Exception("Not possible to encode this message")


def _decode_superdense(q1, q2):
    """
    Return the message encoded into qA with the support of qB.

    Args:
    qA: the qubit the message is encoded into
    qB: the supporting entangled pair

    Returns:
        string: A string of decoded message.

    """
    q1.cnot(q2)
    q1.H()

    # Measure
    a = q1.measure()
    b = q2.measure()

    return str(a) + str(b)
