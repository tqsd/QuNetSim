import time

from cqc.pythonLib import CQCConnection, qubit

import sys
import threading
import queue

sys.path.append("..")
from protocol import protocols

measurements_arr = []
teleported_qubits = []
data_arr = []


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


def process_message(incoming):
    global gBob, qubits

    m = incoming[0]

    if m == 0:
        q = gBob.recvQubit()
        meas = q.measure()
        print('Measured qubit', meas)

    elif m == 1:
        qubits.append(gBob.recvEPR())

    elif m == protocols.TELEPORT:
        a = incoming[1]
        b = incoming[2]
        qB = qubits.pop()
        if b == 1:
            qB.X()
        if a == 1:
            qB.Z()

        teleported_qubits.append(qB)
        print("Qubit arrived")
        time.sleep(0.5)

    elif m == 3:
        message = protocols.receive_superdense(gBob)
        to_print = "Receiver {}: The message Alice sent was: {}".format(gBob.name, message)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

    elif m == 5:

        packet_size = incoming[1]
        checksum_size = incoming[2]
        transmission_succ = True

        if len(teleported_qubits) != (packet_size + checksum_size):
            transmission_succ = False

        else:
            check_size = int(packet_size / checksum_size)

            counter = 0
            i = 0
            while i < packet_size:
                for j in range(check_size):
                    teleported_qubits[i + j].cnot(teleported_qubits[packet_size + counter])

                counter = counter + 1
                i = i + check_size

            for i in range(checksum_size):
                measurement = teleported_qubits[packet_size + i].measure()
                print("Measured qubit ", measurement)

                if measurement != 0:
                    transmission_succ = False

            if transmission_succ:

                for i in range(packet_size):
                    measurement = teleported_qubits[i].measure()
                    data_arr.append(measurement)

                print("Received data is : ", data_arr)


def process_queue():
    while True:
        global stop_thread, message_queue
        if stop_thread:
            return

        if not message_queue.empty():
            m = message_queue.get()
            process_message(m)


def listen_for_messages():
    global gBob, stop_thread
    while True:
        if stop_thread:
            return
        print('bob listening')
        try:
            incoming = list(gBob.recvClassical(timout=1))
            print('bob received classical')
            message_queue.put(incoming)
        except RuntimeError:
            print('no incoming messages at time interval ')


message_queue = queue.Queue()
qubits = []
stop_thread = False
gBob = None


def main():
    with CQCConnection("Bob") as Bob:
        global gBob
        gBob = Bob

        # Start listening for classical messages
        DaemonThread(target=listen_for_messages)
        DaemonThread(target=process_queue)

        start_time = time.time()
        # time for bob to Listen in seconds
        listen_time = 15
        # Listen for 15 seconds and stop
        while (time.time() - start_time) < listen_time:
            pass

        global stop_thread
        stop_thread = True
        print("Stopped listening")


main()
