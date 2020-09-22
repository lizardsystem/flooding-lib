#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from optparse import make_option

from django.core.management.base import BaseCommand
from lizard_worker.file_logging import setFileHandler, removeFileHandlers
from lizard_worker.worker.worker import Worker
from lizard_worker.worker.action_queue import ActionQueue
from lizard_worker.worker.broker_connection import BrokerConnection

import logging
log = logging.getLogger("worker.management.logging_worker")


class Command(BaseCommand):
    """
    Manages the messages in queues.
    - soorts meaasges by priority and timestamp

    De worker starts by default with next args:
    - --worker_nr=500
    - --task_code=500
    - --log_level=DEBUG
    """

    help = ("Example: bin/django task_worker_new "\
            "--task_code 120 "\
            "--log_level DEBUG "\
            "--worker_nr 1")

    option_list = BaseCommand.option_list + (
        make_option('--task_code',
                    help='tasks that worker must perform',
                    type='str',
                    default='500'),
        make_option('--worker_nr',
                    help='use this if you need more than one '\
                        'uitvoerder on this workstation',
                    type='str',
                    default='500'),
        make_option('--log_level',
                    help='logging level to send to messaging broker',
                    type='str',
                    default='DEBUG'),)

    def handle(self, *args, **options):

        numeric_level = getattr(logging, options["log_level"].upper(), None)
        if not isinstance(numeric_level, int):
            log.error("Invalid log level: %s" % options["log_level"])
            numeric_level = 10

        broker = BrokerConnection()
        connection = broker.connect_to_broker()

        removeFileHandlers()
        setFileHandler('queue')

        if connection is None:
            log.error("Could not connect to broker.")
            return
        # TODO CREATE ActionPreority
        action = ActionPriority(connection,
                                options["task_code"])

        queue_worker = Worker(connection,
                              options["task_code"],
                              action)
        queue_worker.run_worker()
