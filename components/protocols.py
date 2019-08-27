from cqc.pythonLib import qubit
import time

# DATA TYPES
from components.logger import Logger
from components.network import Network

CLASSICAL = '00'
QUANTUM = '11'
SIGNAL = '10'

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
        return _send_epr(sender, receiver)
    elif protocol == SEND_SUPERDENSE:
        return _send_superdense(sender, receiver, payload)
    elif protocol == REC_SUPERDENSE:
        return _rec_superdense(sender, receiver, payload)
    elif protocol == RELAY:
        return _relay_message(receiver, packet)
    elif protocol == REC_TELEPORT_EPR:
        return _rec_teleport_epr(sender, receiver, payload)
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
    packet = encode(host_sender.host_id, receiver, REC_CLASSICAL, message, CLASSICAL)
    host_receiver = network.get_host(receiver)

    if not (host_receiver or host_sender):
        # TODO: create a meaningful exception
        raise Exception

    network.send(packet)


def _rec_classical(sender, receiver, payload):
    # Assume the payload is the classical message
    _send_ack(sender, receiver)
    return payload


def _send_teleport(sender, receiver, q):
    host_sender = network.get_host(sender)
    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        _send_epr(sender, receiver)

    epr_teleport = host_sender.get_epr(receiver)

    q.cnot(epr_teleport['q'])
    q.H()

    m1 = q.measure()
    m2 = epr_teleport['q'].measure()

    data = {'measurements': [m1, m2], 'q_id': epr_teleport['q_id']}
    packet = encode(sender, receiver, REC_TELEPORT, data, CLASSICAL)
    network.send(packet)


def _rec_teleport(sender, receiver, payload):
    host_receiver = network.get_host(receiver)

    q = host_receiver.get_epr(sender, q_id=payload['q_id'])

    a = payload['measurements'][0]
    b = payload['measurements'][1]

    # Apply corrections
    if b == 1:
        q.X()
    if a == 1:
        q.Z()

    m = q.measure()
    Logger.get_instance().log('Teleported qubit is: ' + str(m))

    _send_ack(sender, receiver)


def _send_teleport_epr(sender, receiver, node, q):
    host_sender = network.get_host(sender)
    # host_receiver = network.get_host(receiver)
    if not network.shares_epr(sender, receiver):
        print('Sent epr')
        _send_epr(sender, receiver)

    epr_teleport = host_sender.get_epr(receiver)
    q.cnot(epr_teleport['q'])
    q.H()

    m1 = q.measure()
    m2 = epr_teleport['q'].measure()
    packet = encode(sender, receiver, REC_TELEPORT_EPR, [m1, m2, node], CLASSICAL)
    network.send(packet)


def _rec_teleport_epr(sender, receiver, payload):
    host_receiver = network.get_host(receiver)
    q1 = host_receiver.get_epr(sender)['q']
    a = payload[0]
    b = payload[1]
    epr_host = payload[2]

    # Apply corrections
    if b == 1:
        q1.X()
    if a == 1:
        q1.Z()

    host_receiver.add_epr(epr_host, q1)

    # Logger.get_instance().log('Teleported qubit is: ' + str(m))

    _send_ack(sender, receiver)


def _send_epr(sender, receiver):
    route = network.get_route(sender, receiver)
    host_sender = network.get_host(sender)
    receiver_name = network.get_host_name(receiver)
    if len(route) == 2:
        q = host_sender.cqc.createEPR(receiver_name)
        q_id = host_sender.add_epr(receiver, q)
        packet = encode(sender, receiver, REC_EPR, payload={'q_id': q_id}, payload_type=CLASSICAL)
        network.send(packet)
    else:
        for i in range(len(route) - 1):
            _send_epr(route[i], route[i + 1])

        for i in range(len(route) - 2):
            q = None

            while q is None:
                q = (network.get_host(route[i + 1])).get_epr(route[0])

            _send_teleport_epr(route[i + 1], route[i + 2], sender, q['q'])

        q2 = host_sender.get_epr(route[1])
        host_sender.add_epr(receiver, q2['q'], q2['q_id'])


def _rec_epr(sender, receiver, payload):
    host_receiver = network.get_host(receiver)
    q = host_receiver.cqc.recvEPR()
    host_receiver.add_epr(sender, q, q_id=payload['q_id'])
    return _send_ack(sender, receiver)


def _send_ack(sender, receiver):
    return


def _send_superdense(sender, receiver, payload):
    host_sender = network.get_host(sender)

    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        _send_epr(sender, receiver)

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
    m = _decode_superdense(qA, qB)
    return m


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
