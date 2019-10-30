from cqc.pythonLib import qubit

# DATA TYPES
from components.logger import Logger
from components.network import Network

# CONSTANTS
GENERATE_EPR_IF_NONE = 'generate_epr_if_none'
AWAIT_ACK = 'await_ack'
SEQUENCE_NUMBER = 'sequence_number'
PAYLOAD = 'payload'
PAYLOAD_TYPE = 'payload_type'
SENDER = 'sender'
RECEIVER = 'receiver'
PROTOCOL = 'protocol'

network = Network.get_instance()

# QUBIT TYPES
EPR = 0
DATA = 1

# DATA KINDS
SIGNAL = 'signal'
CLASSICAL = 'classical'
QUANTUM = 'quantum'
ACK = 'ACK'
NACK = 'NACK'

# PROTOCOL IDs
REC_EPR = 'rec_epr'
SEND_EPR = 'send_epr'
REC_TELEPORT = 'rec_teleport'
SEND_TELEPORT = 'send_teleport'
REC_SUPERDENSE = 'rec_superdense'
SEND_SUPERDENSE = 'send_superdense'
REC_CLASSICAL = 'rec_classical'
SEND_CLASSICAL = 'send_classical'
RELAY = 'relay'
SEND_QUBIT = 'send_qubit'
REC_QUBIT = 'rec_qubit'


def process(packet):
    """
    Decodes the packet and processes the packet according to the protocol in the packet header.

    Args:
        packet (dict): Packet to be processed.

    Returns:
        Returns what protocol function returns.

    """

    protocol = packet[PROTOCOL]
    if protocol == SEND_TELEPORT:
        return _send_teleport(packet)
    elif protocol == REC_TELEPORT:
        return _rec_teleport(packet)
    elif protocol == SEND_CLASSICAL:
        return _send_classical(packet)
    elif protocol == REC_CLASSICAL:
        return _rec_classical(packet)
    elif protocol == REC_EPR:
        return _rec_epr(packet)
    elif protocol == SEND_EPR:
        return _send_epr(packet)
    elif protocol == SEND_SUPERDENSE:
        return _send_superdense(packet)
    elif protocol == REC_SUPERDENSE:
        return _rec_superdense(packet)
    elif protocol == SEND_QUBIT:
        return _send_qubit(packet)
    elif protocol == REC_QUBIT:
        return _rec_qubit(packet)
    elif protocol == RELAY:
        return _relay_message(packet)
    else:
        Logger.get_instance().error('protocol not defined')


def encode(sender, receiver, protocol, payload=None, payload_type='', sequence_num=-1, await_ack=False):
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
        await_ack(bool): If the sender should await an ACK
    Returns:
         dict: Encoded packet

    """

    packet = {
        SENDER: sender,
        RECEIVER: receiver,
        PROTOCOL: protocol,
        PAYLOAD_TYPE: payload_type,
        PAYLOAD: payload,
        SEQUENCE_NUMBER: sequence_num,
        AWAIT_ACK: await_ack
    }
    return packet


def _relay_message(packet):
    """
    Reduce TTL of network packet and if TTL > 0, sends the message to be relayed to the next
    node in the network and modifies the header.

    Args:
        packet (dict): Packet to be relayed

    """
    packet['TTL'] -= 1
    if packet['TTL'] != 0:
        network.send(packet)
    else:
        Logger.get_instance().log('TTL Expired on packet')


def _send_classical(packet):
    """
    Sends a classical message to another host.

    Args:
       packet (dict): The packet in which to transmit.

    """
    packet[PROTOCOL] = REC_CLASSICAL
    network.send(packet)


def _rec_classical(packet):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an
    ACK message to receiver.

    Args:
        packet (dict): The packet in which to receive.

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """
    if packet[PAYLOAD] == ACK:
        Logger.get_instance().log(packet[RECEIVER] + " received ACK from " + packet[SENDER]
                                  + " with sequence number " + str(packet[SEQUENCE_NUMBER]))

    if packet[AWAIT_ACK]:
        _send_ack(packet[SENDER], packet[RECEIVER], packet[SEQUENCE_NUMBER])

    return {'sender': packet[SENDER], 'message': packet[PAYLOAD], 'sequence_number': packet[SEQUENCE_NUMBER]}


def _send_qubit(packet):
    """
    Transmit the qubit
    Args:
        packet (dict): The packet in which to transmit.
    """
    packet[PROTOCOL] = REC_QUBIT
    network.send(packet)


def _rec_qubit(packet):
    """
    Receive a packet containing qubit information (qubit is transmitted externally)

    Args:
        packet (dict): The packet in which to receive.
    """
    Logger.get_instance().log(
        packet[RECEIVER] + ' received qubit ' + packet[PAYLOAD][0]['q_id'] + ' from ' + packet[SENDER])
    if packet[AWAIT_ACK]:
        _send_ack(packet[SENDER], packet[RECEIVER], packet[SEQUENCE_NUMBER])


def _send_teleport(packet):
    """
    Does the measurements for teleportation of a qubit and sends the measurement results to another host.

    Args:
        packet (dict): The packet in which to transmit.
    """

    if 'node' in packet[PAYLOAD]:
        node = packet[PAYLOAD]['node']
    else:
        node = packet[SENDER]

    if 'type' in packet[PAYLOAD]:
        q_type = packet[PAYLOAD]['type']
    else:
        q_type = DATA

    q_id = None

    q = packet[PAYLOAD]['q']

    host_sender = network.get_host(packet[SENDER])
    if GENERATE_EPR_IF_NONE in packet[PAYLOAD] and packet[PAYLOAD][GENERATE_EPR_IF_NONE]:
        if not network.shares_epr(packet[SENDER], packet[RECEIVER]):
            print('!!! GENERATING EPR PAIR !!!')
            Logger.get_instance().log(
                'No shared EPRs - Generating one between ' + packet[SENDER] + " and " + packet[RECEIVER])
            q_id, _ = host_sender.send_epr(packet[RECEIVER], await_ack=True, block=True)

    if 'q_id' in packet[PAYLOAD]:
        epr_teleport = host_sender.get_epr(packet[RECEIVER], packet[PAYLOAD]['q_id'], wait=10)
    else:
        if q_id is not None:
            epr_teleport = host_sender.get_epr(packet[RECEIVER], q_id, wait=10)
        else:
            epr_teleport = host_sender.get_epr(packet[RECEIVER], wait=10)
    assert epr_teleport is not None
    q.cnot(epr_teleport['q'])
    q.H()

    m1 = q.measure()
    m2 = epr_teleport['q'].measure()
    data = {
        'measurements': [m1, m2],
        'type': q_type,
        'node': node
    }
    if q_type == EPR:
        data['q_id'] = packet[PAYLOAD]['q_id']
    else:
        data['q_id'] = epr_teleport['q_id']

    if 'o_seq_num' in packet[PAYLOAD]:
        data['o_seq_num'] = packet[PAYLOAD]['o_seq_num']
    if 'ack' in packet[PAYLOAD]:
        data['ack'] = packet[PAYLOAD]['ack']

    packet[PAYLOAD] = data
    packet[PROTOCOL] = REC_TELEPORT
    network.send(packet)


def _rec_teleport(packet):
    """
    Receives a classical message and applies the required operations to EPR pair entangled with the sender to
    retrieve the teleported qubit.

    Args:
        packet (dict): The packet in which to receive.
    """
    host_receiver = network.get_host(packet[RECEIVER])
    payload = packet[PAYLOAD]
    q_id = payload['q_id']

    q = host_receiver.get_epr(packet[SENDER], q_id, wait=10)
    if q is None:
        # TODO: what to do when fails
        return
    q = q['q']
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

    if packet[AWAIT_ACK]:
        if 'o_seq_num' in payload and 'ack' in payload:
            _send_ack(epr_host, packet[RECEIVER], payload['o_seq_num'])

        _send_ack(packet[SENDER], packet[RECEIVER], packet[SEQUENCE_NUMBER])


def _send_epr(packet):
    """
    Sends an EPR to another host in the network.

    Args:
        packet (dict): The packet in which to transmit.
    """
    packet[PROTOCOL] = REC_EPR
    network.send(packet)


def _rec_epr(packet):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an ACK message to
    receiver.

    Args:
        packet (dict): The packet in which to receive.

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """
    payload = packet[PAYLOAD]
    receiver = packet[RECEIVER]
    sender = packet[SENDER]
    host_receiver = network.get_host(receiver)

    q = host_receiver.cqc.recvEPR()
    if payload is None:
        host_receiver.add_epr(sender, q)
    else:
        host_receiver.add_epr(sender, q, q_id=payload['q_id'], blocked=payload['block'])

    if packet[AWAIT_ACK]:
        _send_ack(sender, receiver, packet[SEQUENCE_NUMBER])


def _send_ack(sender, receiver, seq_number):
    """
    Send an acknowledge message from the sender to the receiver.
    Args:
        sender (string): The sender ID
        receiver (string): The receiver ID
        seq_number (string): The sequence number which to ACK
    """
    Logger.get_instance().log('sending ACK:' + str(seq_number) + ' from ' + receiver + " to " + sender)
    host_receiver = network.get_host(receiver)
    host_receiver.send_ack(sender, seq_number)


def _send_superdense(packet):
    """
    Encodes and sends a qubit to send a superdense message.

    Args:
        packet (dict): The packet in which to transmit.
    """
    sender = packet[SENDER]
    receiver = packet[RECEIVER]
    host_sender = network.get_host(sender)

    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        host_sender.send_epr(receiver, await_ack=True)

    q_superdense = host_sender.get_epr(receiver, wait=10)
    if q_superdense is None:
        Logger.get_instance().log('Failed to get EPR with ' + sender + " and " + receiver)
        raise Exception("couldn't encode superdense")

    _encode_superdense(packet[PAYLOAD], q_superdense['q'])
    packet[PAYLOAD] = [q_superdense]
    packet[PROTOCOL] = REC_SUPERDENSE
    packet[PAYLOAD_TYPE] = QUANTUM
    network.send(packet)


def _rec_superdense(packet):
    """
    Receives a superdense qubit and decodes it.

    Args:
       packet (dict): The packet in which to receive.

    Returns:
        dict: A dictionary consisting of decoded superdense message and sequence number
    """
    receiver = packet[RECEIVER]
    sender = packet[SENDER]
    payload = packet[PAYLOAD]

    host_receiver = network.get_host(receiver)

    q1 = host_receiver.get_data_qubit(sender, payload[0]['q_id'], wait=10)
    q2 = host_receiver.get_epr(sender, payload[0]['q_id'], wait=10)

    assert q1 is not None and q2 is not None

    if packet[AWAIT_ACK]:
        _send_ack(packet[SENDER], packet[RECEIVER], packet[SEQUENCE_NUMBER])

    return {'sender': packet[SENDER], 'message': _decode_superdense(q1['q'], q2['q']),
            SEQUENCE_NUMBER: packet[SEQUENCE_NUMBER]}


def _add_checksum(sender, qubits, size_per_qubit=2):
    """
    Generate a set of qubits that represent a quantum checksum for the set of qubits *qubits*
    Args:
        sender: The sender name
        qubits: The set of qubits to encode
        size: The size of the checksum per qubit (i.e. 1 qubit encoded into *size*)

    Returns:
        list: A list of qubits that are encoded for *qubits*
    """
    i = 0
    check_qubits = []
    while i < len(qubits):
        check = qubit(sender)
        j = 0
        while j < size_per_qubit:
            qubits[i + j].cnot(check)
            j += 1

        check_qubits.append(check)
        i += size_per_qubit
    return check_qubits


def _encode_superdense(message, q):
    """
    Encode qubit q with the 2 bit message.

    Args:
        message: the message to encode
        q: the qubit to encode the message
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
    Return the message encoded into q1 with the support of q2.

    Args:
    q1: the qubit the message is encoded into
    q1: the supporting entangled pair

    Returns:
        string: A string of decoded message.

    """
    q1.cnot(q2)
    q1.H()

    # Measure
    a = q1.measure()
    b = q2.measure()

    return str(a) + str(b)
