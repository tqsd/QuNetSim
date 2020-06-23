from qunetsim.objects import Logger, Packet, Message, Qubit
from qunetsim.components.network import Network
from qunetsim.utils.constants import Constants
import numpy as np
import random

network = Network.get_instance()


def encode(sender, receiver, protocol, payload=None, payload_type='', sequence_num=-1, await_ack=False):
    """
    Encodes the data with the sender, receiver, protocol, payload type and sequence number and forms the packet
    with data and the header.
    Args:
        sender(str): ID of the sender
        receiver(str): ID of the receiver
        protocol(str): ID of the protocol of which the packet should be processed.
        payload : The message that is intended to send with the packet. Type of payload depends on the protocol.
        payload_type(str): Type of the payload.
        sequence_num(int): Sequence number of the packet.
        await_ack(bool): If the sender should await an ACK
    Returns:
         (Packet): Encoded packet
    """

    packet = Packet(sender, receiver, protocol, payload_type, payload,
                    sequence_number=sequence_num, await_ack=await_ack)
    return packet


def process(packet):
    """
    Decodes the packet and processes the packet according to the protocol in the packet header.

    Args:
        packet (Packet): Packet to be processed.

    Returns:
        Returns what protocol function returns.

    """

    protocol = packet.protocol
    if protocol == Constants.SEND_TELEPORT:
        return _send_teleport(packet)
    elif protocol == Constants.REC_TELEPORT:
        return _rec_teleport(packet)
    elif protocol == Constants.SEND_CLASSICAL:
        return _send_classical(packet)
    elif protocol == Constants.REC_CLASSICAL:
        return _rec_classical(packet)
    elif protocol == Constants.REC_EPR:
        return _rec_epr(packet)
    elif protocol == Constants.SEND_EPR:
        return _send_epr(packet)
    elif protocol == Constants.SEND_SUPERDENSE:
        return _send_superdense(packet)
    elif protocol == Constants.REC_SUPERDENSE:
        return _rec_superdense(packet)
    elif protocol == Constants.SEND_QUBIT:
        return _send_qubit(packet)
    elif protocol == Constants.REC_QUBIT:
        return _rec_qubit(packet)
    elif protocol == Constants.RELAY:
        return _relay_message(packet)
    elif protocol == Constants.SEND_KEY:
        return _send_key(packet)
    elif protocol == Constants.REC_KEY:
        return _rec_key(packet)
    elif protocol == Constants.SEND_GHZ:
        return _send_ghz(packet)
    elif protocol == Constants.REC_GHZ:
        return _rec_ghz(packet)
    elif protocol == Constants.SEND_BROADCAST:
        return _send_broadcast(packet)
    else:
        Logger.get_instance().error('protocol not defined: ' + str(protocol))


def _relay_message(packet):
    """
    Reduce TTL of network packet and if TTL > 0, sends the message to be relayed to the next
    node in the network and modifies the header.

    Args:
        packet (RoutingPacket): Packet to be relayed

    """
    packet.ttl -= 1
    if packet.ttl != 0:
        network.send(packet)
    else:
        Logger.get_instance().log('TTL Expired on packet')


def _send_broadcast(packet):
    sender = packet.sender
    message = packet.payload
    host_sender = network.get_host(sender)

    for host in network.ARP.keys():
        if sender != host:
            seq_num = host_sender.get_next_sequence_number(host)
            message.seq_num = seq_num
            new_packet = Packet(sender=sender,
                                receiver=host,
                                protocol=Constants.REC_CLASSICAL,
                                payload=message,
                                payload_type=Constants.CLASSICAL,
                                sequence_number=seq_num,
                                await_ack=False)
            network.send(new_packet)


def _send_classical(packet):
    """
    Sends a classical message to another host.

    Args:
       packet (Packet): The packet in which to transmit.

    """
    packet.protocol = Constants.REC_CLASSICAL
    network.send(packet)


def _rec_classical(packet):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an
    ACK message to receiver.

    Args:
        packet (Packet): The packet in which to receive.

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """
    message = packet.payload
    if packet.payload.content == Constants.ACK:
        message = Message(sender=packet.sender, content=Constants.ACK, seq_num=packet.seq_num)
        Logger.get_instance().log(packet.receiver + " received ACK from " + packet.sender
                                  + " with sequence number " + str(packet.seq_num))
    else:
        # Send an ACK msg if seq_num is not -1, as long as not an ACK msg!
        if packet.seq_num != -1:
            _send_ack(packet.sender, packet.receiver, packet.seq_num)

    return message


def _send_qubit(packet):
    """
    Transmit the qubit
    Args:
        packet (Packet): The packet in which to transmit.
    """
    packet.protocol = Constants.REC_QUBIT
    network.send(packet)


def _rec_qubit(packet):
    """
    Receive a packet containing qubit information (qubit is transmitted externally)

    Args:
        packet (Packet): The packet in which to receive.
    """
    from_host = packet.sender
    receiver = packet.receiver
    qubit = packet.payload
    receiver = network.get_host(receiver)
    receiver.add_data_qubit(from_host, qubit)

    Logger.get_instance().log(
        packet.receiver + ' received qubit ' + packet.payload.id + ' from ' + packet.sender)
    # Send ACK if seq_num is not -1

    if packet.seq_num != -1:
        _send_ack(packet.sender, packet.receiver, packet.seq_num)


def _send_teleport(packet):
    """
    Does the measurements for teleportation of a qubit and sends the measurement results to another host.

    Args:
        packet (Packet): The packet in which to transmit.
    """

    if 'node' in packet.payload:
        node = packet.payload['node']
    else:
        node = packet.sender

    if 'type' in packet.payload:
        q_type = packet.payload['type']
    else:
        q_type = Constants.DATA

    q = packet.payload['q']
    host_sender = network.get_host(packet.sender)

    if Constants.GENERATE_EPR_IF_NONE in packet.payload and packet.payload[Constants.GENERATE_EPR_IF_NONE]:
        if not network.shares_epr(packet.sender, packet.receiver):
            Logger.get_instance().log(
                'No shared EPRs - Generating one between ' + packet.sender + " and " + packet.receiver)
            host_sender.send_epr(packet.receiver, q_id=q.id, await_ack=True, block=True)

    if 'eq_id' in packet.payload:
        epr_teleport = host_sender.get_epr(packet.receiver, packet.payload['eq_id'], wait=Constants.WAIT_TIME)
    else:
        epr_teleport = host_sender.get_epr(packet.receiver, wait=Constants.WAIT_TIME)

    assert epr_teleport is not None
    q.cnot(epr_teleport)
    q.H()

    m1 = q.measure()
    m2 = epr_teleport.measure()

    data = {
        'measurements': [m1, m2],
        'type': q_type,
        'node': node
    }

    if q_type == Constants.EPR:
        data['q_id'] = packet.payload['eq_id']
        data['eq_id'] = packet.payload['eq_id']
    else:
        data['q_id'] = q.id
        data['eq_id'] = epr_teleport.id

    if 'o_seq_num' in packet.payload:
        data['o_seq_num'] = packet.payload['o_seq_num']
    if 'ack' in packet.payload:
        data['ack'] = packet.payload['ack']

    packet.payload = data
    packet.protocol = Constants.REC_TELEPORT
    network.send(packet)


def _rec_teleport(packet):
    """
    Receives a classical message and applies the required operations to EPR pair entangled with the sender to
    retrieve the teleported qubit.

    Args:
        packet (Packet): The packet in which to receive.
    """
    host_receiver = network.get_host(packet.receiver)
    payload = packet.payload
    q_id = payload['q_id']
    eq_id = payload['eq_id']

    q = host_receiver.get_epr(packet.sender, eq_id, wait=Constants.WAIT_TIME)
    if q is None:
        raise Exception("failed to get EPR")

    a = payload['measurements'][0]
    b = payload['measurements'][1]
    epr_host = payload['node']

    # Apply corrections
    if a == 1:
        q.Z()
    if b == 1:
        q.X()

    if payload['type'] == Constants.EPR:
        host_receiver.add_epr(epr_host, q)

    elif payload['type'] == Constants.DATA:
        host_receiver.add_data_qubit(epr_host, q, q_id=q_id)

    # Always send ACK!
    if 'o_seq_num' in payload and 'ack' in payload:
        _send_ack(epr_host, packet.receiver, payload['o_seq_num'])

    # Send an ACK if sequence number is not -1
    if packet.seq_num != -1:
        _send_ack(packet.sender, packet.receiver, packet.seq_num)


def _send_epr(packet):
    """
    Sends an EPR to another host in the network.

    Args:
        packet (Packet): The packet in which to transmit.
    """
    packet.protocol = Constants.REC_EPR
    network.send(packet)


def _rec_epr(packet):
    """
    Receives a classical message packet , parses it into sequence number and message and sends an ACK message to
    receiver.

    Args:
        packet (Packet): The packet in which to receive.

    Returns:
        dict : A dictionary consisting of 'message' and 'sequence number'
    """
    payload = packet.payload
    receiver = packet.receiver
    sender = packet.sender
    host_receiver = network.get_host(receiver)
    q = host_receiver.backend.receive_epr(host_receiver.host_id,
                                          sender_id=sender,
                                          q_id=payload['q_id'],
                                          block=payload['blocked'])
    host_receiver.add_epr(sender, q)
    # Send an ACK if sequence number is not -1
    if packet.seq_num != -1:
        _send_ack(sender, receiver, packet.seq_num)


def _send_ack(sender, receiver, seq_number):
    """
    Send an acknowledge message from the sender to the receiver.
    Args:
        sender (str): The sender ID
        receiver (str): The receiver ID
        seq_number (int): The sequence number which to ACK
    """
    Logger.get_instance().log('sending ACK:' + str(seq_number + 1) + ' from ' + receiver + " to " + sender)
    host_receiver = network.get_host(receiver)
    host_receiver.send_ack(sender, seq_number)


def _send_superdense(packet):
    """
    Encodes and sends a qubit to send a superdense message.

    Args:
        packet (Packet): The packet in which to transmit.
    """
    sender = packet.sender
    receiver = packet.receiver
    host_sender = network.get_host(sender)

    if not network.shares_epr(sender, receiver):
        Logger.get_instance().log('No shared EPRs - Generating one between ' + sender + " and " + receiver)
        q_id, _ = host_sender.send_epr(receiver, await_ack=True, block=True)
        assert q_id is not None
        q_superdense = host_sender.get_epr(receiver, q_id=q_id, wait=Constants.WAIT_TIME)

    else:
        q_superdense = host_sender.get_epr(receiver)

    if q_superdense is None:
        Logger.get_instance().log('Failed to get EPR with ' + sender + " and " + receiver)
        raise Exception("couldn't encode superdense")

    _encode_superdense(packet.payload, q_superdense)

    # change ID, so that at receiving they are not the same
    q_superdense.id = "E" + q_superdense.id
    packet.payload = q_superdense
    packet.protocol = Constants.REC_SUPERDENSE
    packet.payload_type = Constants.QUANTUM
    network.send(packet)


def _rec_superdense(packet):
    """
    Receives a superdense qubit and decodes it.

    Args:
       packet (Packet): The packet in which to receive.

    Returns:
        dict: A dictionary consisting of decoded superdense message and sequence number
    """
    receiver = packet.receiver
    sender = packet.sender
    q1 = packet.payload
    host_receiver = network.get_host(receiver)

    # the shared EPR id is the DATA id without the first letter.
    q2 = host_receiver.get_epr(sender, q1.id[1:], wait=Constants.WAIT_TIME)

    assert q1 is not None
    assert q2 is not None

    # Send ACK if seq_num is not -1
    if packet.seq_num != -1:
        _send_ack(packet.sender, packet.receiver, packet.seq_num)

    return Message(packet.sender, _decode_superdense(q1, q2), packet.seq_num)


def _send_key(packet):
    receiver = network.get_host(packet.receiver)
    sender = network.get_host(packet.sender)
    key_size = packet.payload[Constants.KEYSIZE]

    packet.protocol = Constants.KEY
    network.send(packet)

    secret_key = np.random.randint(2, size=key_size)
    msg_buff = []
    sender.qkd_keys[receiver.host_id] = secret_key.tolist()
    sequence_nr = 0
    # iterate over all bits in the secret key.
    for bit in secret_key:
        ack = False
        while not ack:
            # get a random base. 0 for Z base and 1 for X base.
            base = random.randint(0, 1)

            # create qubit
            q_bit = Qubit(sender)
            # Set qubit to the bit from the secret key.
            if bit == 1:
                q_bit.X()

            # Apply basis change to the bit if necessary.
            if base == 1:
                q_bit.H()

            # Send Qubit to Receiver
            sender.send_qubit(receiver.host_id, q_bit, await_ack=True)
            # Get measured basis of Receiver
            message = sender.get_next_classical_message(receiver.host_id, msg_buff, sequence_nr)
            # Compare to send basis, if same, answer with 0 and set ack True and go to next bit,
            # otherwise, send 1 and repeat.
            if message == "%d:%d" % (sequence_nr, base):
                ack = True
                sender.send_classical(receiver.host_id, ("%d:0" % sequence_nr), await_ack=True)
            else:
                ack = False
                sender.send_classical(receiver.host_id, ("%d:1" % sequence_nr), await_ack=True)

            sequence_nr += 1


def _rec_key(packet):
    """
    Receive a QKD key.

    Args:
        packet (Packet): The incoming packet
    """
    receiver = network.get_host(packet.receiver)
    sender = network.get_host(packet.sender)
    key_size = packet.payload[Constants.KEYSIZE]

    msg_buff = []

    sequence_nr = 0
    received_counter = 0
    key_array = []

    while received_counter < key_size:
        # decide for a measurement base
        measurement_base = random.randint(0, 1)

        # wait for the qubit
        q_bit = receiver.get_data_qubit(sender.host_id, wait=Constants.WAIT_TIME)
        while q_bit is None:
            q_bit = receiver.get_data_qubit(sender.host_id, wait=Constants.WAIT_TIME)

        # measure qubit in right measurement basis
        if measurement_base == 1:
            q_bit.H()
        bit = q_bit.measure()

        # Send sender the base in which receiver has measured
        receiver.send_classical(sender.host_id, "%d:%d" % (sequence_nr, measurement_base), await_ack=True)

        # get the return message from sender, to know if the bases have matched
        msg = receiver.get_next_classical_message(sender.host_id, msg_buff, sequence_nr)

        # Check if the bases have matched
        if msg == ("%d:0" % sequence_nr):
            received_counter += 1
            key_array.append(bit)
        sequence_nr += 1

    key = key_array
    receiver.qkd_keys[sender.host_id] = key


def _send_ghz(packet):
    """
    Gets GHZ qubits and distributes the to all hosts.
    One qubit is stored in own storage.

    Args:
        packet (Packet): The incoming packet

    """
    host_list = packet.payload[Constants.HOSTS]
    qubits = packet.payload[Constants.QUBITS]
    sender = packet.sender
    await_ack = packet.await_ack
    seq_num_list = packet.seq_num

    for host, qubit, seq_num in zip(host_list, qubits, seq_num_list):
        new_packet = Packet(sender=sender,
                            receiver=host,
                            protocol=Constants.REC_GHZ,
                            payload=qubit,
                            payload_type=Constants.QUANTUM,
                            sequence_number=seq_num,
                            await_ack=await_ack)
        network.send(new_packet)


def _rec_ghz(packet):
    """
    Receives a GHZ state and stores it in quantum storage.

    Args:
        packet (Packet): The incoming packet
    """
    from_host = packet.sender
    receiver = packet.receiver
    qubit = packet.payload
    receiver = network.get_host(receiver)
    receiver.add_ghz_qubit(from_host, qubit)

    # Send ACK if seq_num is not -1
    if packet.seq_num != -1:
        _send_ack(packet.sender, packet.receiver, packet.seq_num)


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
        q1 (Qubit): The qubit the message is encoded into
        q1 (Qubit): The supporting entangled pair

    Returns:
        (str): A string of decoded message.
    """
    q1.cnot(q2)
    q1.H()

    # Measure
    a = q1.measure()
    b = q2.measure()

    return "%d%d" % (a, b)
