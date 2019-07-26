import time

from cqc.pythonLib import CQCConnection, qubit

import sys
import threading
import queue

sys.path.append("..")
from protocol import protocols


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


def process_message(m):
    global gBob
    if m == 0:
        q = gBob.recvQubit()
        meas = q.measure()
        print('Measured qubit', meas)

    elif m == 1:
        q = gBob.recvEPR()
        meas = q.measure()
        print('Measured EPR', meas)


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
            m = list(gBob.recvClassical(timout=1))[0]
            print('bob received classical')
            message_queue.put(m)
        except RuntimeError:
            print('no incoming messages at time interval ', t)


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
        listen_time = 10
        # Listen for 10 seconds and stop
        while (time.time() - start_time) < listen_time:
            pass

        global stop_thread
        stop_thread = True
        print("Stopped listening")


main()
