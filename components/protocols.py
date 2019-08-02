from cqc.pythonLib import qubit

# DATA TYPES
from components.network import Network

CLASSICAL = '00'
QUANTUM = '11'

# SIGNALS
ACK = '1111'
NACK = '0000'

# PROTOCOL IDs
RECEIVE_EPR = '00000000'
RECEIVE_TELEPORT = '00000001'
SEND_TELEPORT = '00000010'
RECEIVE_SUPERDENSE = '00000011'
SEND_UDP = '00000100'
TERMINATE_UDP = '00000101'
SEND_ACK = '00000110'
REC_ACK = '00000111'
SEND_CLASSICAL = '00001000'
REC_CLASSICAL = '00001001'

network = Network()


def process(header):
    print('incoming: ', header)
    sender, receiver, protocol, payload, payload_type = _parse_message(header)

    if protocol == SEND_TELEPORT:
        return _send_teleport(sender, receiver, payload)
    elif protocol == RECEIVE_TELEPORT:
        return _receive_teleport(sender, receiver)
    elif protocol == SEND_CLASSICAL:
        return _send_classical(sender, receiver, payload)
    elif protocol == REC_CLASSICAL:
        return _rec_classical(payload)
    else:
        print('protocol not defined')


def _parse_message(message):
    message_data = str(message[0])
    sender = str(message_data[0:8])
    receiver = str(message_data[8:16])
    protocol = str(message_data[16:24])
    payload_type = str(message_data[24:26])
    payload = message[1]
    return sender, receiver, protocol, payload, payload_type


def _send_classical(sender, receiver, message):
    host_sender = network.get_host(sender)
    packet = encode(host_sender.host_id, receiver, REC_CLASSICAL, message, CLASSICAL)
    host_receiver = network.get_host(receiver)

    if not (host_receiver or host_sender):
        # TODO: create meaningful exception
        raise Exception

    print('sending')

    # We avoid using CQCs classical input
    network.send(packet, receiver)
    # host_sender.cqc.sendClassical(host_receiver.cqc.name, packet)


def _rec_classical(payload):
    # Assume the payload is the classical message
    return payload


def encode(sender, receiver, protocol, payload, payload_type):
    packet = []
    if payload_type == CLASSICAL:
        header = sender + receiver + protocol + payload_type
        packet = [header, payload]
    elif payload_type == QUANTUM:
        # TODO: Think about the differences between classical and quantum
        header = sender + receiver + protocol + payload_type
        packet = [header, payload]

    return packet


def _send_teleport(sender, receiver, q):
    sender = network.get_host(sender)

    sender.sendClassical(receiver, [RECEIVE_EPR])
    qA = sender.createEPR(receiver)
    q.cnot(qA)
    q.H()
    data = [q.measure(), qA.measure()]
    packet = encode(sender, receiver, RECEIVE_TELEPORT, data, CLASSICAL)
    sender.sendClassical(receiver, packet)


def _receive_teleport(sender, receiver):
    receiver = network.get_host(receiver)
    qB = receiver.recvEPR()
    data = receiver.recvClassical()
    message = list(data)
    a = message[0]
    b = message[1]

    # Apply corrections
    if b == 1:
        qB.X()
    if a == 1:
        qB.Z()

    _send_ack(sender, receiver)

    return qB


def _send_ack(host, destination):
    pass


def _encode_superdense(message, q):
    """
    Return a qubit encoded with the message message.

    Params:
    message -- the message to encode
    qubit -- the qubit to encode the message

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

    return q


def _decode_superdense(qA, qB):
    """
    Return the message encoded into qA with the support of qB.

    Params:
    qA -- the qubit the message is encoded into
    qB -- the supporting entangled pair

    """
    qA.cnot(qB)
    qA.H()

    # Measure
    a = qA.measure()
    b = qB.measure()

    return str(a) + str(b)


def _send_superdense(sender, message, receiver):
    qA = sender.createEPR(receiver)
    _encode_superdense(message, qA)
    sender.sendQubit(qA, receiver)


def _receive_superdense(receiver, should_decode=True):
    qB = receiver.recvEPR()
    qA = receiver.recvQubit()
    if should_decode:
        return _decode_superdense(qA, qB)
    else:
        return [qA, qB]


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
