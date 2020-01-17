import logging

FORMAT = '%(asctime)s: %(message)s'
logging.basicConfig(format=FORMAT)


class Logger:
    __instance = None

    @staticmethod
    def get_instance():
        if Logger.__instance is None:
            Logger()
        return Logger.__instance

    def __init__(self):
        if Logger.__instance is None:
            self.logger = logging.getLogger('qu_net_sim')
            self.logger.setLevel(logging.INFO)
            Logger.__instance = self
        else:
            raise Exception('this is a singleton class')

    def warn(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def log(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)
