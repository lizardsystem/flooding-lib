#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from optparse import make_option

from django.core.management.base import BaseCommand
from lizard_worker.file_logging import setFileHandler, removeFileHandlers
from lizard_worker.file_logging import setLevelToAllHandlers
from lizard_worker.worker.worker import Worker
from lizard_worker.worker.action_supervisor import ActionSupervisor
from lizard_worker.worker.broker_connection import BrokerConnection
from lizard_worker.worker.message_logging_handler import AMQPMessageHandler

import logging
log = logging.getLogger("worker.management.supervisor_worker")


class Command(BaseCommand):
    """
    Run supervisor worker. Use the worker to start task-workers remotely.
    Only for unix systems.
    """

    help = ("Example: bin/django lw_supervisor_worker "\
            "--queue_code 900 "\
            "--log_level DEBUG "\
            "--worker_nr 1")

    option_list = BaseCommand.option_list + (
        make_option('--queue_code',
                    help='queue to consume',
                    type='str'),
        make_option('--log_level',
                    help='logging level',
                    type='str',
                    default='DEBUG'),
        make_option('--worker_nr',
                    help='unique number per node, use this if you need more than one',
                    type='int',
                    default=1000))

    def handle(self, *args, **options):

        if not options["queue_code"]:
            log.error("Expected a queue_code argument, use --help.")
            return

        numeric_level = getattr(logging, options["log_level"].upper(), None)
        if not isinstance(numeric_level, int):
            log.error("Invalid log level: %s" % options["log_level"])
            numeric_level = 10

        broker = BrokerConnection()
        connection = broker.connect_to_broker()

        removeFileHandlers()
        setFileHandler(options["worker_nr"])
        setLevelToAllHandlers(numeric_level)

        if connection is None:
            log.error("Could not connect to broker.")
            return

        action = ActionSupervisor(connection,
                                  options["queue_code"],
                                  options["worker_nr"],
                                  numeric_level)

        logging.handlers.AMQPMessageHandler = AMQPMessageHandler
        broker_logging_handler = logging.handlers.AMQPMessageHandler(
            action, numeric_level)
        action.set_broker_logging_handler(broker_logging_handler)
        
        task_worker = Worker(connection,
                             options["queue_code"],
                             action,
                             options["worker_nr"])
        log.info("Start worker.")
        task_worker.run_worker()
        removeFileHandlers()
