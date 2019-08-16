# -*- coding: utf-8 -*-
"""
PanGalactic loggers
"""
from builtins import object
import logging
from logging.handlers import RotatingFileHandler
import os, sys


def get_loggers(home, name, console=False, debug=False):
    """
    Get application logger and error logger.

    Args:
        home (str): full path to app home directory (log files will be
                written into a 'log' subdirectory)
        console (bool): (default: False)
            if True, send log messages to stdout
            if False, send stdout/stderr to log files
        debug (bool):  if True, sets level to debug
    """
    logdir = os.path.join(home, 'log')
    # make sure logdir exists ...
    if not os.path.exists(logdir):
        os.makedirs(logdir, mode=0o775)
    log_filename = os.path.join(logdir, name+'_log')
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(log_filename,
                                  maxBytes=250000,
                                  backupCount=10)
    logger.addHandler(handler)
    message_format = u"%(asctime)s %(message)s"
    date_time_format = u"%Y-%m-%d %H:%M"
    formatter = logging.Formatter(message_format, date_time_format)
    handler.setFormatter(formatter)

    error_log_filename = os.path.join(logdir, name+'_error_log')
    error_logger = logging.getLogger(name+'_error')
    error_logger.setLevel(logging.INFO)
    if debug:
        error_logger.setLevel(logging.DEBUG)
    error_handler = RotatingFileHandler(error_log_filename,
                                        maxBytes=250000,
                                        backupCount=10)
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    if console:
        logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        error_logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    return logger, error_logger


class LoggerWriter(object):
    def __init__(self, logger, level): 
        self.logger = logger
        self.level = level 

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

    def flush(self): 
        pass

