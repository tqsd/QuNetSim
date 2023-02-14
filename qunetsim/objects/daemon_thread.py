import threading


class DaemonThread(threading.Thread):
    """ A Daemon thread that runs a task until completion and then exits. """

    def __init__(self, target, args=None, kwargs=None):
        if kwargs is not None:
            super().__init__(target=target, daemon=True, args=args, kwargs=kwargs)
        elif args is not None:
            super().__init__(target=target, daemon=True, args=args) 
        else:
            super().__init__(target=target, daemon=True)
        self.start()
