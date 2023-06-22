import threading


def is_thread_alive(thread_name):
    for thread in threading.enumerate():
        if thread_name == thread:
            return thread.isAlive()


class DaemonThread(threading.Thread):
    """ A Daemon thread that runs a task until completion and then exits. """

    def __init__(self, target, args=None):
        if args is not None:
            super().__init__(target=target, daemon=True, args=args)
        else:
            super().__init__(target=target, daemon=True)
        self.start()
