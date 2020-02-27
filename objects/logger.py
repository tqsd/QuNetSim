import logging

FORMAT = '%(asctime)s: %(message)s'
logging.basicConfig(format=FORMAT)

class Logger():
    __instance = None
    DISABLED = True

    @staticmethod
    def get_instance():
        if Logger.__instance is None:
            Logger()
        return Logger.__instance

    def __init__(self,file=None):
        if Logger.__instance is None:
            # if file is not None:
            #     logging.basicConfig(format=FORMAT, filename=file)
            # if file is None:
            #     logging.basicConfig(format=FORMAT)
            self.logger = logging.getLogger('qu_net_sim')
            self.logger.setLevel(logging.INFO)
            Logger.__instance = self
        else:
            raise Exception('this is a singleton class')

    def warn(self, message):
        if not Logger.DISABLED:
            self.logger.warning(message)

    def error(self, message):
        if not Logger.DISABLED:
            self.logger.error(message)

    def log(self, message):
        if not Logger.DISABLED:
            self.logger.info(message)

    def debug(self, message):
        if not Logger.DISABLED:
            self.logger.debug(message)
