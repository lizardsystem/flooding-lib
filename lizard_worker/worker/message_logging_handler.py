#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

import logging


class AMQPMessageHandler(logging.Handler):
    """
    Sends the loggings to message broker.
    """

    def __init__(self, action, numeric_level=10):
        logging.Handler.__init__(self, level=numeric_level)
        self.action = action

    def emit(self, record):
        self.action.send_logging_message(record.msg)
