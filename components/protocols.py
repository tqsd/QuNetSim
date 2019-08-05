from cqc.pythonLib import qubit

# DATA TYPES
from components.network import Network

CLASSICAL = '00'
QUANTUM = '11'

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

network = Network.get_instance()


def process(header):
    sender, receiver, protocol, payload, payload_type = _parse_message(header)

    if protocol == SEND_TELEPORT:
        return _send_teleport(sender, receiver, payload)
    elif protocol == REC_TELEPORT:
        return _rec_teleport(sender, receiver)
    elif protocol == SEND_CLASSICAL:
        return _send_classical(sender, receiver, payload)
    elif protocol == REC_CLASSICAL:
        return _rec_classical(sender, receiver, payload)
    elif protocol == REC_EPR:
        return _rec_epr(sender, receiver)
    elif protocol == SEND_EPR:
        return _send_epr(sender, receiver)
    else:
        print('protocol not defined')


def encode(sender, receiver, protocol, payload='', payload_type=''):
    packet = []
    if payload_type == CLASSICAL:
        header = sender + receiver + protocol + payload_type
        packet = [header, payload]
    # elif payload_type == QUANTUM:
    else:
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


def _rec_classical(sender, receiver, payload):
    # Assume the payload is the classical message
    _send_ack(sender, receiver)
    return payload


def _send_teleport(sender, receiver, q):
    host_sender = network.get_host(sender)

    # ask network if there is an EPR pair between sender / receiver
    # if not, generate it
    # else teleport
    pass


def _rec_teleport(sender, receiver):
    # receiver = network.get_host(receiver)
    # qB = receiver.recvEPR()
    # data = receiver.recvClassical()
    # message = list(data)
    # a = message[0]
    # b = message[1]
    #
    # # Apply corrections
    # if b == 1:
    #     qB.X()
    # if a == 1:
    #     qB.Z()
    #
    # _send_ack(sender, receiver)
    #
    # return qB
    pass


def _send_epr(sender, receiver):
    host_sender = network.get_host(sender)
    receiver_name = network.get_host_name(receiver)

    packet = encode(sender, receiver, REC_EPR)
    network.send(packet, receiver)

    q = host_sender.cqc.createEPR(receiver_name)
    # TODO: wait for ACK before adding epr
    host_sender.add_epr(receiver, q)


def _rec_epr(sender, receiver):
    host_receiver = network.get_host(receiver)
    q = host_receiver.cqc.recvEPR()
    host_receiver.add_epr(sender, q)
    _send_ack(sender, receiver)


def _send_ack(sender, receiver):
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
    pass


def _receive_superdense(receiver, should_decode=True):
    pass


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
