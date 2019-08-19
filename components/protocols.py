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
SEND_EPR = '00001011'
REC_TELEPORT = '00000001'
SEND_TELEPORT = '00000010'
REC_SUPERDENSE = '00000011'
SEND_UDP = '00000100'
TERMINATE_UDP = '00000101'
SEND_ACK = '00000110'
REC_ACK = '00000111'
SEND_CLASSICAL = '00001000'
REC_CLASSICAL = '00001001'
SEND_SUPERDENSE = '00001010'
RELAY = '00001011'

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
        return _rec_epr(sender, receiver)
    elif protocol == SEND_EPR:
        return _send_epr(sender, receiver)
    elif protocol == SEND_TELEPORT:
        return _send_teleport(sender, receiver, payload)
    elif protocol == SEND_SUPERDENSE:
        return _send_superdense(sender, receiver, payload)
    elif protocol == REC_SUPERDENSE:
        return _rec_superdense(sender, receiver)
    elif protocol == RELAY:
        _relay_packet(payload)
    else:

        print('protocol not defined')


def encode(sender, receiver, protocol, payload=None, payload_type=''):
    packet = []
    if payload_type == CLASSICAL or payload_type == SIGNAL:
        header = sender + receiver + protocol + payload_type
        packet = [header, payload]
    elif payload_type == QUANTUM:
        for q in payload:
            host_sender = network.get_host(sender)
            host_sender.cqc.sendQubit(q, network.get_host_name(receiver))
            host_receiver = network.get_host(receiver)
            qr = host_receiver.cqc.recvQubit()
            host_receiver.add_data_qubit(sender, qr)

        # TODO: Think about the differences between classical and quantum
        header = sender + receiver + protocol + payload_type
        packet = [header, payload]

    return packet


def _parse_message(message):
    message_data = str(message[0])
    sender = str(message_data[0:8])
    receiver = str(message_data[8:16])
    protocol = str(message_data[16:24])
    payload_type = str(message_data[24:26])
    payload = message[1]

    return sender, receiver, protocol, payload, payload_type


def _relay_packet(payload):
    # payload is a transport_layer_packet
    network.send()

    pass


def _send_classical(sender, receiver, message):
    host_sender = network.get_host(sender)
    packet = encode(host_sender.host_id, receiver, REC_CLASSICAL, message, CLASSICAL)
    host_receiver = network.get_host(receiver)

    if not (host_receiver or host_sender):
        # TODO: create meaningful exception
        raise Exception

    network.send(packet)


def _rec_classical(sender, receiver, payload):
    # Assume the payload is the classical message
    _send_ack(sender, receiver)
    return payload


def _send_teleport(sender, receiver, q):
    host_sender = network.get_host(sender)
    if not network.shares_epr(sender, receiver):
        print('Sent epr')
        _send_epr(sender, receiver)

    epr_teleport = host_sender.get_epr(receiver)
    q.cnot(epr_teleport)
    q.H()

    m1 = q.measure()
    m2 = epr_teleport.measure()
    packet = encode(sender, receiver, REC_TELEPORT, [m1, m2], CLASSICAL)
    network.send(packet)


def _rec_teleport(sender, receiver, payload):
    host_receiver = network.get_host(receiver)

    q1 = host_receiver.get_epr(sender)

    a = payload[0]
    b = payload[1]

    # Apply corrections
    if b == 1:
        q1.X()
    if a == 1:
        q1.Z()

    m = q1.measure()
    Logger.get_instance().debug('Teleported qubit is: ' + str(m))

    _send_ack(sender, receiver)


def _send_epr(sender, receiver):
    host_sender = network.get_host(sender)
    receiver_name = network.get_host_name(receiver)

    packet = encode(sender, receiver, REC_EPR, payload_type=CLASSICAL)
    network.send(packet)

    q = host_sender.cqc.createEPR(receiver_name)
    # TODO: wait for ACK before adding epr
    host_sender.add_epr(receiver, q)


def _rec_epr(sender, receiver):
    host_receiver = network.get_host(receiver)
    q = host_receiver.cqc.recvEPR()
    host_receiver.add_epr(sender, q)
    # print('did this 12')
    return _send_ack(sender, receiver)


def _send_ack(sender, receiver):
    return


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


def _send_superdense(sender, receiver, message):
    host_sender = network.get_host(sender)

    if not network.shares_epr(sender, receiver):
        print('Sent epr')
        _send_epr(sender, receiver)

    q_superdense = host_sender.get_epr(receiver)
    _encode_superdense(message, q_superdense)
    time.sleep(0.2)
    packet = encode(sender, receiver, REC_SUPERDENSE, [q_superdense], QUANTUM)
    network.send(packet)


def _rec_superdense(sender, receiver):
    host_receiver = network.get_host(receiver)
    qA = host_receiver.get_data_qubit(sender)
    qB = host_receiver.get_epr(sender)
    m = _decode_superdense(qA, qB, )
    Logger.get_instance().debug("Received message is " + m)
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
