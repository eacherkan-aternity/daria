import logging
import os
import sys

from logging.handlers import RotatingFileHandler


def get_logger(name, level=logging.DEBUG, stdout=False):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_handler = RotatingFileHandler(os.environ.get('LOG_FILE_PATH', 'agent.log'), maxBytes=2000)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    if stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    return logger
