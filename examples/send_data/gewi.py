import random
import time
import math

from qunetsim.components import Host, Network
from qunetsim.objects import Logger, Qubit
from qunetsim.backends import EQSNBackend

Logger.DISABLED = True
# this is for QNS to stay in sync
DISCRETE_TIME_STEP = 0
# this is the probability that NO data arrives in a time slot, -- if there
# is currently no frame coming in.
PROB = 0.3
# this is the data arrival probablity for dense coding
DENSE_PROB = 0.9
# ...
EPR_FRAME_LENGTH = 48
# ...
DATA_FRAME_LENGTH = 96
# transmit acknowledgement from receiver to sender after getting a data framesWITH
WITH_ACK = False

messages = [
    "It~must~be~~", "considered~~", "that~there~~", "is~nothing~~", "more~~~~~~~~", "difficult~~~", "to~carry~out",
    "~nor~more~~~",
    "doubtful~of~", "success~nor~", "more~~~~~~~~", "dangerous~~~", "to~handle~~~", "than~to~~~~~", "initiate~a~~",
    "new~order~of",
    "~things~~for", "~the~~~~~~~~", "reformer~has", "~enemies~in~", "all~those~~~", "who~profit~~", "by~the~old~~",
    "order~~and~~",
    "only~~~~~~~~", "lukewarm~~~~", "defenders~in", "~all~those~~", "who~would~~~", "profit~by~~~", "the~new~~~~~",
    "order~~this~",
    "lukewarmness", "~arising~~~~", "partly~from~", "the~~~~~~~~~", "incredulity~", "of~mankind~~", "who~does~not",
    "~truly~~~~~~",
    "believe~in~~", "anything~new", "~until~they~", "actually~~~~", "have~~~~~~~~", "experience~~", "of~it~~~~~~~"]


def string_to_binary(st):
    binary_chars = ''.join("0" + format(ord(i), 'b') for i in st)
    if len(binary_chars) != 96:
        raise Exception(
            "binary string of length ",
            len(binary_chars),
            " detected. String reads as",
            st)
    return binary_chars


def binary_to_string(st):
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(st)] * 8))


def dens_encode(q: Qubit, bits: str):
    # assumption: qubit q is entangled with another qubit q' which resides at receiver
    # bits is a two-bit string
    # think of dense_encode as an optical device at the sender side, where each qubit has to pass through the optical device
    # I, X, Y, Z are another way of writing the Pauli matrices
    if bits == '00':
        q.I()
    elif bits == '10':
        q.Z()
    elif bits == '01':
        q.X()
    elif bits == '11':
        q.X()
        q.Z()
    else:
        raise Exception('Bad input')
    return q


def dense_decode(stored_epr_half: Qubit, received_qubit: Qubit):
    received_qubit.cnot(stored_epr_half)
    received_qubit.H()
    meas = [None, None]
    meas[0] = received_qubit.measure()
    meas[1] = stored_epr_half.measure()
    return str(meas[0]) + str(meas[1])


def encode(q: Qubit, bit: str):
    if bit == "0":
        q.I()
    elif bit == "1":
        q.X()
    else:
        raise Exception("Bad input")
    return q


def decode(q: Qubit):
    meas = None
    meas = q.measure()
    return str(meas)


def parse_message_dense(bits: str):
    # check whether string is of even length ... omitted here
    out = []
    for i in range(int(len(bits) / 2)):
        out.append(bits[2 * i: 2 * i + 2])
    return out


def parse_message(bits: str):
    # check whether string is of even length ... omitted here
    out = []
    for i in range(int(len(bits))):
        out.append(bits[i: i + 1])
    return out


def transmit_bit_frame(bit_frame: str, sender_host, receiver_host_id):
    # the sender needs to check whether it has enough entanglement shared with
    # the receiver to handle the entire frame using dense coding
    eb = len(sender_host.get_epr_pairs(receiver_host_id))
    # print("entanglement buffer has",eb,"EPR pairs")
    # we need a header to inform the receiver what's coming - qubits for data
    # transmission or qubits to be stored into entanglement buffer
    number_of_transmitted_qubits = 0
    headerQubit = Qubit(sender_host)
    # print("SENDER: generated headerQubit with id",headerQubit._id)
    sender_host.send_qubit(receiver_host_id, headerQubit, no_ack=True)
    # print("header was sent")
    # time.sleep(DISCRETE_TIME_STEP)
    number_of_transmitted_qubits += 1
    protocol_type = 0
    offset = 1
    if eb > len(bit_frame) / 2 - offset:
        protocol_type = 1
        msgs = parse_message_dense(bit_frame)
        for i in range(len(msgs)):
            q = sender_host.get_epr(receiver_host_id)
            # here we apply the envisioned optical device to the 2-bit piece of the message
            qout = dens_encode(q, str(msgs[i]))
            sender_host.send_qubit(receiver_host_id, qout, no_ack=True)
            number_of_transmitted_qubits += 1
            # time.sleep(DISCRETE_TIME_STEP)
    else:
        protocol_type = 2
        msgs = parse_message(bit_frame)
        for i in range(len(msgs)):
            q = Qubit(sender_host)
            # here we apply the envisioned optical device to the 2-bit piece of the message
            qout = encode(q, str(msgs[i]))
            sender_host.send_qubit(receiver_host_id, qout, no_ack=True)
            number_of_transmitted_qubits += 1
            # time.sleep(DISCRETE_TIME_STEP)
    print("SENDER: transmitted data frame with", number_of_transmitted_qubits, "qubits")
    return protocol_type


def transmit_epr_frame(sender_host, receiver_host_id):
    # count the total number of transmitted qubits for logging purpose
    number_of_transmitted_qubits = 0
    # we need a header to inform the receiver what's coming - qubits for data
    # transmission or qubits to be stored into entanglement buffer
    headerQubit = Qubit(sender_host)
    # put header qubit into state "e_1"
    headerQubit.X()
    sender_host.send_qubit(receiver_host_id, headerQubit, no_ack=True)
    # time.sleep(DISCRETE_TIME_STEP)

    for i in range(EPR_FRAME_LENGTH):
        # generate two qubits
        q_sender = Qubit(sender_host)
        q_receiver = Qubit(sender_host)
        # entangle both qubits so that they are in EPR state
        q_sender.H()
        q_sender.cnot(q_receiver)
        # now store one half of the entangled state at the sender
        sender_host.add_epr(receiver_host_id, q_sender)
        # send the other half to the receicer
        sender_host.send_qubit(receiver_host_id, q_receiver, no_ack=True)
        number_of_transmitted_qubits += 1
        # time.sleep(DISCRETE_TIME_STEP)
        # print("sharing ",i," epr pairs now!")
    # now sender has transmitted an entire EPR frame to the receiver
    print("SENDER: transmitted EPR frame with", number_of_transmitted_qubits, "qubits")
    return 0


def pause():
    duration = 0
    while True:
        incoming = random.random()
        if incoming < PROB:
            duration += DISCRETE_TIME_STEP
        else:
            break
    return duration


def performance_check(host_A, host_B):
    print(time.perf_counter())
    q = Qubit(host_A)
    print("sender qubit initialized, starting counter")
    print(time.perf_counter())
    # qout = encode( q, "0" )
    host_A.send_qubit(host_B.host_id, q, no_ack=True)
    qin = host_B.get_data_qubit(host_A.host_id, wait=-1)
    res = qin.measure()
    print(time.perf_counter())
    q_sender = Qubit(host_A)
    q_receiver = Qubit(host_A)
    # entangle both qubits so that they are in EPR state
    q_sender.H()
    q_sender.cnot(q_receiver)
    # now store one half of the entangled state at the sender
    host_A.add_epr(host_B.host_id, q_sender)
    # send the other half to the receicer
    host_A.send_qubit(host_B.host_id, q_receiver, no_ack=True)
    stored_epr_half = host_B.get_data_qubit(host_A.host_id, wait=-1)
    print("epr established, starting counter")
    print(time.perf_counter())
    q = host_B.get_epr(host_A.host_id)
    host_A.send_qubit(host_B.host_id, q_sender, no_ack=True)
    received_qubit = host_B.get_data_qubit(host_A.host_id, wait=-1)
    received_qubit.cnot(stored_epr_half)
    received_qubit.H()
    meas = [None, None]
    meas[0] = received_qubit.measure()
    meas[1] = stored_epr_half.measure()
    q = Qubit(host_A)
    qout = encode(q, "0")
    host_A.send_qubit(host_B.host_id, qout)
    qin = host_B.get_data_qubit(host_A.host_id, wait=-1)
    res = qin.measure()
    print(time.perf_counter())


def arrival_pattern():
    MSGS = len(messages)
    message_counter = 0
    pattern = []
    time = 0
    print("generating pattern for", MSGS, "messages")
    while message_counter < MSGS:
        next_pause = 0
        while True:
            incoming = random.random()
            if incoming < PROB:
                next_pause += 1
            else:
                break
        message_counter += 1
        type = random.random()
        if type < DENSE_PROB:
            next_pause += DATA_FRAME_LENGTH / 2
        else:
            next_pause += DATA_FRAME_LENGTH
        time += next_pause
        pattern.append(time)
    return pattern


def protocol_sender(host: Host, receiver: str, image):
    # count the number of transmitted frames
    current_index = 0
    # mBuffer holds the messages that have arrived in the sender buffer already
    mBuffer = []
    # discrete time steps, sending one qubit costs one time step
    time_steps_elapsed = 0
    #
    last_data_time_index = 0
    #
    pattern = arrival_pattern()
    print(pattern)
    received_message_index = 0

    bits = [bin(int(b, base=16))[2:] for b in image]

    while current_index < len(messages):
        # don't ever set PROB to 1 ...
        # print(current_index)
        for i in range(len(pattern)):
            if pattern[i] >= last_data_time_index and pattern[i] < time_steps_elapsed:
                mBuffer.append(messages[received_message_index])
                received_message_index += 1
                print("message number ", received_message_index, " just came in")

        last_data_time_index = time_steps_elapsed
        print("SENDER: time is ", last_data_time_index, "buffer is", mBuffer)
        if len(mBuffer) == 0:
            # generate entanglement if pause is long enough
            # assuming here the sender knows the duration of the pause in advance!
            print("SENDER: transmit 1 EPR frame")
            # wait the remaining discrete time steps until the end of the pause
            done = transmit_epr_frame(host, receiver)
            time_steps_elapsed += EPR_FRAME_LENGTH
        else:
            # have to transmit right away
            print("SENDER: sending data")
            # pick the next message from buffer
            string_to_send = mBuffer[0]
            # delete this message from buffer
            mBuffer.pop(0)
            # transmit the message
            binary_string = string_to_binary(string_to_send)
            protocol_type = transmit_bit_frame(binary_string, host, receiver)
            if WITH_ACK:
                ack = host.get_next_classical(receiver, wait=-1)
                print(ack.content)
            # increment time counter depending on protocol that was used
            if protocol_type == 1:
                time_steps_elapsed += DATA_FRAME_LENGTH / 2
            else:
                time_steps_elapsed += DATA_FRAME_LENGTH
            print("SENDER: message with index", current_index, "was transmited")
            # increment message counter
            current_index += 1
    print("SENDER: finished")


def protocol_receiver(host: Host, sender: str):
    current_index = 0
    dense_counter = 0
    data_frame_counter = 0
    epr_frame_counter = 0
    received_messages = []
    while data_frame_counter < len(messages):
        number_of_received_qubits = 0
        q = host.get_data_qubit(sender, wait=-1)
        number_of_received_qubits += 1
        print("RECEIVER: got header qubit with id", q._id)
        bitstring = ""
        switch = None
        switch = q.measure()
        # print("RECEIVER: switch received command", switch)
        if switch == 0:
            data_frame_counter += 1
            # here the sender intends to transmit data
            # receiver has to check its EPR buffer to decide how to decode
            epr_buffer = host.get_epr_pairs(sender)
            # here is some weird leftover problem. Code works with offset = 0 although
            # offset = -1 would be correct
            offset = 1

            start_timer = time.time()
            hhh = 0
            if len(epr_buffer) > math.ceil(DATA_FRAME_LENGTH / 2) - offset:
                # here we have enough stored EPR halfes, so we decode using dense coding
                print("RECEIVER: ", len(epr_buffer), "stored EPR halfes, using dense decoder")
                counter = 0
                while counter < math.ceil(DATA_FRAME_LENGTH / 2):
                    stored_half = host.get_epr(sender)
                    arriving_half = host.get_data_qubit(sender, wait=-1)
                    number_of_received_qubits += 1
                    ggg = time.time()
                    decoded_bits = dense_decode(arriving_half, stored_half)
                    print(f'----{time.time() - ggg} seconds to decode')
                    bitstring += decoded_bits
                    counter += 1
                    hhh += 1
                dense_counter += 1
            else:
                # here we decode one bit per qubit
                print("RECEIVER: ", len(epr_buffer), "stored epr halfes, using ordinary decoder")
                counter = 0
                while counter < DATA_FRAME_LENGTH:
                    arriving_qubit = host.get_data_qubit(sender, wait=-1)
                    number_of_received_qubits += 1
                    decoded_bit = decode(arriving_qubit)
                    bitstring += decoded_bit
                    hhh += 1
                    counter += 1
            print(f"RECEIVER: Decoding {hhh} qubits took {time.time() - start_timer} seconds")

            # print("RECEIVER: received",number_of_received_qubits,"qubits")
            # print("RECEIVER: received bit string is",bitstring)
            print("RECEIVER:", binary_to_string(bitstring))
            received_messages.append(binary_to_string(bitstring))
            if WITH_ACK:
                host.send_classical(sender, data_frame_counter)
        elif switch == 1:
            # here we store all incoming qubits as EPR halfes
            print("RECEIVER: receiving frame for EPR buffer")
            epr_frame_counter += 1
            counter = 0
            while counter < EPR_FRAME_LENGTH:
                arriving_half = host.get_data_qubit(sender, wait=-1)
                host.add_epr(sender, arriving_half)
                counter += 1
            print("RECEIVER: stored EPR frame")
        else:
            print(switch)
            raise Exception("receiver was not able to decode header")
        current_index += 1
    print(
        "RECEIVER received ",
        data_frame_counter,
        " data frames, out of which ",
        dense_counter,
        " frames were transmitted using dense coding. In addition, ",
        epr_frame_counter,
        "epr frames were received.")
    print("RECEIVER received the following messages:", received_messages)
    # expected stats:
    # @ PROB = 0.95


def main():
    backend = EQSNBackend()

    network = Network.get_instance()

    network.start(backend=backend)

    host_A = Host('A', backend)
    host_A.add_connection('B')
    host_A.start()
    host_B = Host('B', backend)
    host_B.add_connection('A')
    host_B.start()

    host_A.delay = 0.01
    host_B.delay = 0.01

    network.add_hosts([host_A, host_B])


    host_A.run_protocol(protocol_sender, (host_B.host_id))
    host_B.run_protocol(protocol_receiver, (host_A.host_id,), blocking=True)

    network.stop(True)


if __name__ == '__main__':
    main()
