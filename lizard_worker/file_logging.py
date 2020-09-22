
import logging
import os

from logging.handlers import RotatingFileHandler
from django.conf import settings


def setFileHandler(worker_nr=0):
    """Create new file handler with specific filename."""
    TAIL_LOG = os.path.join(
        getattr(settings, 'BUILDOUT_DIR', ''),
        'var', 'log', '%s_worker_tail.log' % worker_nr)
    handler = RotatingFileHandler(TAIL_LOG, maxBytes=4096, backupCount=1)
    logging.getLogger().addHandler(handler)


def removeFileHandlers():
    """ Remove all existing file handlers from root logger. """
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler):
            logging.getLogger().removeHandler(handler)


def setLevelToAllHandlers(level=0):
    """ Set logging level to existing handlers."""
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)
