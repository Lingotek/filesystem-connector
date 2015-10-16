import logging
import sys
from constants import LOG_FN

_logger = logging.getLogger()
_file_handler = logging.FileHandler(LOG_FN)  # todo maybe have path to where logs stored
_console_handler = logging.StreamHandler(sys.stdout)

_file_handler.setLevel(logging.DEBUG)


logger = _logger

def set_log_level(level):
    logger.setLevel(getattr(logging, level))
