import random
import time
import math

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import threading

from qunetsim.components import Host, Network
from qunetsim.objects import Logger, Qubit
from qunetsim.backends import SimpleStabilizerBackend, EQSNBackend

from messages import binary
import mylogging
import myanimation
import data_conversion
import coding

Logger.DISABLED = True
# The following are the technical parameters one needs to fix
# this is the length of an EPR frame
EPR_FRAME_LENGTH = 16
# by default, a data frame is twice as large as an EPR frame
DATA_FRAME_LENGTH = EPR_FRAME_LENGTH * 2

# the following three parameters are imortant for visualization
VISUALIZATION = True
# discrete time step is chosen such as to let the sender operate approximately as fast as the receiver - this variable depends on your computer
DISCRETE_TIME_STEP = 0.0
# this is the maximum number of seconds after which the next data frame arrives. Arrival times are evenly distributed on [0, MAX_WAITING_TIME]
# Quick calculation:
# For a data frame length of 32, and DISCRETE_TIME_STEP=0.1, it takes around 3.2 seconds to transmit a frame. Thus any value above 7 seconds can activate the EPR queue. Values above 20s lead to almost-always dense coding
MAX_WAITING_TIME = 17
# transmit acknowledgement from receiver to sender after receiving a frame. If this is active, the visualization makes much more sense.
WITH_ACK = True
# if a maximum number of EPR pairs can be stored, then the visualization becomes simplified
E_BUFFER_SIZE = 2 * EPR_FRAME_LENGTH
# below are global variables that we need for the visualization
BUFFER_STATUS = 0
RECEIVED_FRAMES = 0
TRANSMITTED_FRAMES = 0
RECEIVED_BITS = 0
TRANSMITTED_BITS = 0
E_BUFFER_SENDER = 0
E_BUFFER_RECEIVER = 0
TRANSM_TYPE = "NONE"


# this is what the sender does when it wants to transmit data
def transmit_bit_frame(bit_frame: str, sender_host, receiver_host_id):
    global E_BUFFER_SENDER
    global TRANSM_TYPE
    global TRANSMITTED_BITS
    global BUFFER_STATUS
    # the sender needs to check whether it has enough entanglement shared with the receiver to handle the entire frame using dense coding
    epr_buffer = len(sender_host.get_epr_pairs(receiver_host_id))
    mylogging.log("epr_buffer", "entanglement buffer has " + str(epr_buffer) + " EPR pairs")
    # we need a header to inform the receiver what's coming - qubits for data transmission or qubits to be stored into entanglement buffer
    number_of_transmitted_qubits = 0
    headerQubit = Qubit(sender_host)
    mylogging.log("header_info", "SENDER: generated headerQubit with id " + str(headerQubit._id))
    sender_host.send_qubit(receiver_host_id, headerQubit)
    number_of_transmitted_qubits += 1
    time.sleep(DISCRETE_TIME_STEP)
    protocol_type = 0
    offset = 1
    if epr_buffer > len(bit_frame) / 2 - offset:
        TRANSM_TYPE = "DENSE"
        protocol_type = 1
        msgs = data_conversion.parse_message_dense(bit_frame)
        for i in range(len(msgs)):
            q = sender_host.get_epr(receiver_host_id)
            # here we apply the envisioned optical device to the 2-bit piece of the message
            qout = coding.dens_encode(q, str(msgs[i]))
            sender_host.send_qubit(receiver_host_id, qout)
            time.sleep(DISCRETE_TIME_STEP)
            eb = sender_host.get_epr_pairs(receiver_host_id)
            TRANSMITTED_BITS += 2
            E_BUFFER_SENDER = len(eb)
            BUFFER_STATUS -= 2
            number_of_transmitted_qubits += 1
        TRANSMITTED_BITS = 0
    else:
        TRANSM_TYPE = "ORDINARY"
        protocol_type = 2
        msgs = data_conversion.parse_message(bit_frame)
        for i in range(len(msgs)):
            q = Qubit(sender_host)
            # here we apply the envisioned optical device to the 2-bit piece of the message
            qout = coding.encode(q, str(msgs[i]))
            sender_host.send_qubit(receiver_host_id, qout)
            time.sleep(DISCRETE_TIME_STEP)
            TRANSMITTED_BITS += 1
            BUFFER_STATUS -= 1
            number_of_transmitted_qubits += 1
        TRANSMITTED_BITS = 0
    # the sender needs to check whether it has enough entanglement shared with the receiver to handle the entire frame using dense coding
    return protocol_type


def transmit_epr_frame(sender_host, receiver_host_id):
    global TRANSM_TYPE
    global E_BUFFER_SENDER
    TRANSM_TYPE = "EPR"
    # count the total number of transmitted qubits for mylogging purpose
    number_of_transmitted_qubits = 0
    # we need a header to inform the receiver what's coming - qubits for data transmission or qubits to be stored into entanglement buffer
    headerQubit = Qubit(sender_host)
    mylogging.log("header_info", "SENDER: generated headerQubit with id " + str(headerQubit._id))
    # put header qubit into state "e_1"
    headerQubit.X()
    sender_host.send_qubit(receiver_host_id, headerQubit)
    time.sleep(DISCRETE_TIME_STEP)
    for i in range(EPR_FRAME_LENGTH):
        # generate two qubits
        q_sender = Qubit(sender_host)
        q_receiver = Qubit(sender_host)
        # entangle both qubits so that they are in EPR state
        q_sender.H()
        q_sender.cnot(q_receiver)
        # now take a note in the epr_store so that sender host knows the epr storage state
        sender_host.add_epr(receiver_host_id, q_sender)
        eb = sender_host.get_epr_pairs(receiver_host_id)
        E_BUFFER_SENDER = len(eb)
        # send the other half to the receicer
        sender_host.send_qubit(receiver_host_id, q_receiver)
        time.sleep(DISCRETE_TIME_STEP)
        number_of_transmitted_qubits += 1
        mylogging.log("epr_buffer", "SENDER: sharing " + str(i) + " epr pairs now!")
    # now sender has transmitted an entire EPR frame to the receiver
    mylogging.log("epr_buffer", "SENDER: transmitted EPR frame with " + str(number_of_transmitted_qubits) + " qubits")
    return 0


def arrival_pattern(frames, max_waiting_time):
    MSGS = len(frames)
    time = 0
    pattern = []
    for i in range(MSGS):
        increment = random.random() * max_waiting_time
        time += increment
        pattern.append(time)
    return pattern


def protocol_sender(host: Host, receiver: str, frames: list):
    global BUFFER_STATUS
    global TRANSMITTED_FRAMES
    global TRANSM_TYPE
    start_time = time.time()
    # count the number of transmitted frames
    current_index = 0
    # mBuffer holds the messages that have arrived in the sender buffer already
    mBuffer = []
    pattern = arrival_pattern(frames, MAX_WAITING_TIME)
    mylogging.log("data_buffer", "There are a total of " + str(len(frames)) + " frames coming in at " + str(
        len(pattern)) + " different times")
    received_message_index = 0
    no_frames = len(frames)
    while current_index < no_frames:
        current_time = time.time()
        # don't ever set PROB to 1 ...
        mylogging.log("data_buffer", "Starting transmission of frame number " + str(current_index))
        fill = True
        while fill and len(pattern) > 0:
            if start_time + pattern[0] <= current_time:
                mBuffer.append(frames[0])
                # remove frames that have been transmitted from the current buffer and from the future arrivals pattern
                frames.pop(0)
                pattern.pop(0)
            else:
                fill = False
        BUFFER_STATUS = len(mBuffer) * DATA_FRAME_LENGTH
        mylogging.log("data_buffer", "SENDER: incoming messages buffer status is " + str(BUFFER_STATUS) + " bits")
        mylogging.log("time", "SENDER: time is " + str(current_time))
        if len(mBuffer) == 0:
            if len(host.get_epr_pairs(receiver)) < E_BUFFER_SIZE:
                mylogging.log("transmission_type", "SENDER: decided to transmit 1 EPR frame")
                done = transmit_epr_frame(host, receiver)
                if WITH_ACK:
                    ack = host.get_next_classical(receiver, wait=-1)
                    mylogging.log("ack",
                                  "SENDER: received EPR frame acknowledgement for frame number: " + str(ack.content))
            else:
                TRANSM_TYPE = "NONE"
                mylogging.log("transmission_type", "SENDER: transmission type is NONE... waiting ...")
                time.sleep(DISCRETE_TIME_STEP)
        else:
            # have to transmit right away
            mylogging.log("data_transmission", "SENDER: sending data")
            # pick the next message from buffer
            binary_string = mBuffer[0]
            # delete this message from buffer
            mBuffer.pop(0)
            # transmit the message
            protocol_type = transmit_bit_frame(binary_string, host, receiver)
            if protocol_type == 1:
                mylogging.log("data_transmission",
                              "SENDER: transmitted data frame number " + str(current_index) + " using DENSE coding")
            else:
                mylogging.log("data_transmission",
                              "SENDER: transmitted data frame number " + str(current_index) + " using ORDINARY coding")
            # increment message counter
            current_index += 1
            TRANSMITTED_FRAMES = current_index
            if WITH_ACK:
                ack = host.get_next_classical(receiver, wait=-1)
                mylogging.log("ack", "SENDER: received data frame acknowledgement for frame number " + str(ack.content))
    mylogging.log("data_transmission", "SENDER: finished. Sent a total of " + str(current_index) + " frames :)")


def protocol_receiver(host: Host, sender: str, frames: list):
    global RECEIVED_FRAMES
    global E_BUFFER_RECEIVER
    global RECEIVED_BITS
    current_index = 0
    dense_counter = 0
    data_frame_counter = 0
    epr_frame_counter = 0
    received_messages = []
    received_sentence = ""
    no_frames = len(frames)
    RECEIVED_BITS = 0
    while data_frame_counter < no_frames:
        mylogging.log("epr_buffer", "RECEIVER: " + str(BUFFER_STATUS))
        number_of_received_qubits = 0
        q = host.get_data_qubit(sender, wait=-1)
        number_of_received_qubits += 1
        mylogging.log("header_info", "RECEIVER: got header qubit with id " + str(q._id))
        bitstring = ""
        switch = None
        switch = q.measure()
        mylogging.log("switch", "RECEIVER: switch received command " + str(switch))
        start_timer = time.time()
        if switch == 0:
            data_frame_counter += 1
            # here the sender intends to transmit data
            # receiver has to check its EPR buffer to decide how to decode, here we use the built-in function to check what's there
            epr_buffer = host.get_epr_pairs(sender)
            # here is some weird leftover problem. Code works with offset = 0 although offset = -1 would be correct
            offset = 1
            if len(epr_buffer) > math.ceil(DATA_FRAME_LENGTH / 2) - offset:
                # here we have enough stored EPR halfes, so we decode using dense coding
                mylogging.log("epr_buffer",
                              "RECEIVER: " + str(len(epr_buffer)) + " stored EPR halfes, using DENSE decoder")
                counter = 0
                while counter < math.ceil(DATA_FRAME_LENGTH / 2):
                    stored_half = host.get_epr(sender)
                    arriving_half = host.get_data_qubit(sender, wait=-1)
                    number_of_received_qubits += 1
                    decoded_bits = coding.dense_decode(arriving_half, stored_half)
                    bitstring += decoded_bits
                    counter += 1
                    eb = host.get_epr_pairs(sender)
                    E_BUFFER_RECEIVER = len(eb)
                    RECEIVED_BITS += 2
                print("decoder", "RECEIVER: DENSE decoding took " + str(time.time() - start_timer) + " seconds")
                dense_counter += 1
            else:
                # here we decode one bit per qubit
                mylogging.log("epr_buffer",
                              "RECEIVER: " + str(len(epr_buffer)) + " stored EPR halfes, using ORDINARY decoder")
                counter = 0
                while counter < DATA_FRAME_LENGTH:
                    arriving_qubit = host.get_data_qubit(sender, wait=-1)
                    number_of_received_qubits += 1
                    decoded_bit = coding.decode(arriving_qubit)
                    RECEIVED_BITS += 1
                    bitstring += decoded_bit
                    counter += 1
                mylogging.log("decoder",
                              "RECEIVER: ORDINARY decoding took " + str(time.time() - start_timer) + " seconds")
            mylogging.log("data_transmission", "RECEIVER: received " + str(number_of_received_qubits) + " qubits")
            mylogging.log("data_transmission", "RECEIVER: received bit string is " + str(bitstring))
            mylogging.log("frame_content", "RECEIVER: frame_content: " + data_conversion.text_from_bits(bitstring))
            received_messages.append(bitstring)
            received_sentence += bitstring
            RECEIVED_BITS = 0
            RECEIVED_FRAMES = data_frame_counter
            if WITH_ACK:
                host.send_classical(sender, data_frame_counter)
        elif switch == 1:
            # here we store all incoming qubits as EPR halfes
            mylogging.log("epr_buffer", "RECEIVER: receiving frame for EPR buffer")
            epr_frame_counter += 1
            counter = 0
            while counter < EPR_FRAME_LENGTH:
                arriving_half = host.get_data_qubit(sender, wait=-1)
                host.add_epr(sender, arriving_half)
                eb = host.get_epr_pairs(sender)
                E_BUFFER_RECEIVER = len(eb)
                counter += 1
            mylogging.log("epr_buffer", "RECEIVER: stored one EPR frame")
            if WITH_ACK:
                host.send_classical(sender, epr_frame_counter)
        else:
            mylogging.log("switch", "switch status is " + str(switch))
            raise Exception("receiver was not able to decode header")
        current_index += 1
    print("RECEIVER received ", data_frame_counter, " data frames, out of which ", dense_counter,
          " frames were transmitted using dense coding. In addition, ", epr_frame_counter, "epr frames were received.")
    print("RECEIVER received the following bit sequence:", received_sentence)
    print("RECEIVER received the following message:", data_conversion.text_from_bits(received_sentence))


def animate(i):
    myanimation.draw(BUFFER_STATUS, DATA_FRAME_LENGTH, E_BUFFER_RECEIVER, E_BUFFER_SENDER, RECEIVED_BITS,
                     RECEIVED_FRAMES, TRANSM_TYPE, TRANSMITTED_BITS, TRANSMITTED_FRAMES)


def show_plot():
    fig = plt.figure()
    ani = animation.FuncAnimation(fig, animate, fargs=(), interval=200)
    plt.show()


def main():
    # generate the arrival times for the payload
    frames = data_conversion.parse(binary, DATA_FRAME_LENGTH)

    simple_backend = SimpleStabilizerBackend()
    # simple_backend = EQSNBackend()

    print(frames)
    # set up the network
    network = Network.get_instance()
    network.start(backend=simple_backend)
    host_A = Host('A', simple_backend)
    host_A.add_connection('B')
    host_A.start()
    host_B = Host('B', simple_backend)
    host_B.add_connection('A')
    host_B.start()
    network.add_hosts([host_A, host_B])
    # start the thread for the visualization
    if VISUALIZATION:
        t = threading.Thread(target=show_plot)
        t.start()
    t1 = host_A.run_protocol(protocol_sender, (host_B.host_id, frames))
    t2 = host_B.run_protocol(protocol_receiver, (host_A.host_id, frames))
    t1.join()
    t2.join()
    network.stop(True)


if __name__ == '__main__':
    main()
