import logging

FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.debug())


class Logger:
    __instance = None

    @staticmethod
    def get_instance():
        if Logger.__instance is None:
            Logger()
        return Logger.__instance

    def __init__(self):
        if Logger.__instance is None:
            Logger.__instance = self
        else:
            raise Exception('this is a singleton class')

    def warn(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)

    def log(self, message):
        logging.info(message)

    def debug(self, message):
        logging.debug(message)
