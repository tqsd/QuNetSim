import threading
from cqc.pythonLib import qubit
import uuid

# DATA TYPES
from components.logger import Logger
from components.network import Network

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

network = Network.get_instance()


def process(packet):
    sender, receiver, protocol, payload, payload_type = _parse_message(packet)
    if protocol == SEND_TELEPORT:
        return _send_teleport(sender, receiver, payload)
    elif protocol == REC_TELEPORT:
        return _rec_teleport(sender, receiver, payload)
    elif protocol == SEND_CLASSICAL:
        return _send_classical(sender, receiver, payload)
    elif protocol == REC_CLASSICAL:
        return _rec_classical(sender, receiver, payload)
    elif protocol == REC_EPR:
        return _rec_epr(sender, receiver, payload)
    elif protocol == SEND_EPR:
        return _send_epr(sender, receiver, payload)
    elif protocol == SEND_SUPERDENSE:
        return _send_superdense(sender, receiver, payload)
    elif protocol == REC_SUPERDENSE:
        return _rec_superdense(sender, receiver, payload)
    elif protocol == RELAY:
        return _relay_message(receiver, packet)
    else:
        Logger.get_instance().error('protocol not defined')


def encode(sender, receiver, protocol, payload=None, payload_type=''):
    packet = {
        'sender': sender,
        'receiver': receiver,
        'protocol': protocol,
        'payload_type': payload_type,
        'payload': payload,
    }
    return packet


def _parse_message(message):
    sender = message['sender']
    receiver = message['receiver']
    protocol = message['protocol']
    payload_type = message['payload_type']
    payload = message['payload']

    return sender, receiver, protocol, payload, payload_type


def _relay_message(receiver, packet):
    packet['TTL'] -= 1
    packet['sender'] = receiver
    packet['receiver'] = packet['payload']['receiver']
    network.send(packet)


def _send_classical(sender, receiver, message):
    host_sender = network.get_host(sender)
    packet = encode(host_sender.host_id, receiver, REC_CLASSICAL, {'message': message}, CLASSICAL)
    host_receiver = network.get_host(receiver)

    if not (host_receiver or host_sender):
        # TODO: create a meaningful exception
        raise Exception

    network.send(packet)


def _rec_classical(sender, receiver, payload):
    # Assume the payload is the classical message
    _send_ack(sender, receiver)
    return {'message': payload['message']}


def _send_teleport(sender, receiver, payload):
    if 'node' in payload:
        node = payload['node']
    else:
        node = sender

    if 'type' in payload:
        q_type = payload['type']
    else:
        q_type = DATA

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
    packet = encode(sender, receiver, REC_TELEPORT, data, CLASSICAL)
    network.send(packet)


def _rec_teleport(sender, receiver, payload):
    host_receiver = network.get_host(receiver)
    q_id = payload['q_id']
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
    if payload is not None:
        payload = {'q_id': payload}

    packet = encode(sender, receiver, REC_EPR, payload=payload, payload_type=CLASSICAL)
    network.send(packet)


def _rec_epr(sender, receiver, payload):
    host_receiver = network.get_host(receiver)
    q = host_receiver.cqc.recvEPR()
    if payload is None:
        host_receiver.add_epr(sender, q)
    else:
        host_receiver.add_epr(sender, q, q_id=payload['q_id'])
    return _send_ack(sender, receiver)


def _send_ack(sender, receiver):
    return


def _send_superdense(sender, receiver, payload):
    host_sender = network.get_host(sender)
    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        _send_epr(sender, receiver, str(uuid.uuid4()))

    # either there is an epr pair already or one is being generated
    q_superdense = host_sender.get_epr(receiver)

    while q_superdense is None:
        q_superdense = host_sender.get_epr(receiver)

    _encode_superdense(payload, q_superdense['q'])
    packet = encode(sender, receiver, REC_SUPERDENSE, [q_superdense], QUANTUM)
    network.send(packet)


def _rec_superdense(sender, receiver, payload):
    host_receiver = network.get_host(receiver)
    qA = host_receiver.get_data_qubit(sender, payload[0]['q_id'])

    if not qA:
        Logger.get_instance().log("no data qubits")
        return

    qB = host_receiver.get_epr(sender, payload[0]['q_id'])
    while qB is None:
        qB = host_receiver.get_epr(sender, payload[0]['q_id'])

    return {'message': _decode_superdense(qA, qB)}


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
    Encode qubit q with the 2 bit message message.

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
