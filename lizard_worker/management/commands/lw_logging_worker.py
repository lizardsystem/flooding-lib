#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from optparse import make_option

from django.core.management.base import BaseCommand
from lizard_worker.file_logging import setFileHandler, removeFileHandlers
from lizard_worker.worker.worker import Worker
from lizard_worker.worker.action_logging import ActionLogging
from lizard_worker.worker.broker_connection import BrokerConnection

import logging
log = logging.getLogger("worker.management.logging_worker")


class Command(BaseCommand):
    """
    Run logging worker. The worker listens to logging
    queue, retrieves the messages and insert they
    into storage.
    """

    help = ("Example: bin/django lw_logging_worker")

    # option_list = BaseCommand.option_list + (
    #     make_option('--queue_code',
    #                 help='logging queue to consume',
    #                 type='str',
    #                 default='logging'),)

    def handle(self, *args, **options):
        queue_code = 'logging'

        broker = BrokerConnection()
        connection = broker.connect_to_broker()

        removeFileHandlers()
        setFileHandler('logging')

        if connection is None:
            log.error("Could not connect to broker.")
            return

        action = ActionLogging()

        logging_worker = Worker(connection,
                                queue_code,
                                action)
        log.info("Start logging worker.")
        logging_worker.run_worker()
