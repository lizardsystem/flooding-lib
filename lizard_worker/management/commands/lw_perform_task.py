import os
from optparse import make_option
import logging #, threading, time, datetime, random, math

from django.core.management.base import BaseCommand
from django.conf import settings

log = logging.getLogger('worker.management.command.perform_task')


class Command(BaseCommand):
    """
    Run the task directly.
    """

    help = ("""\
perform_task.py [options]

for example:
bin/django lw_perform_task --tasktype_id 120 --scenario_id 50 --worker_nr 1
""")

    option_list = BaseCommand.option_list + (
            make_option('--info',
                        help='be sanely informative - the default',
                        action='store_const',
                        dest='loglevel',
                        const=logging.INFO,
                        default=logging.INFO),
            make_option('--debug',
                        help='be verbose',
                        action='store_const',
                        dest='loglevel',
                        const=logging.DEBUG),
            make_option('--quiet',
                        help='log warnings and errors',
                        action='store_const',
                        dest='loglevel',
                        const=logging.WARNING),
            make_option('--extreme-debugging',
                        help='be extremely verbose',
                        action='store_const',
                        dest='loglevel',
                        const=0),
            make_option('--silent',
                        help='log only errors',
                        action='store_const',
                        dest='loglevel',
                        const=logging.ERROR),
            make_option('--tasktype_id',
                        help='tasks that uitvoerder must perform',
                        default=120,
                        type='int'),
            make_option('--scenario_id',
                        help='scenarios',
                        type='int',
                        default=[-1, -1]),
            make_option('--worker_nr',
                        help='use this if you need more than one uitvoerder on this workstation',
                        type='int',
                        default=1))

    def handle(self, *args, **options):
        perform_task_module = __import__(settings.PERFORM_TASK_MODULE,
                                         fromlist="thelist")
        perform_task = getattr(perform_task_module,
                               settings.PERFORM_TASK_FUNCTION)
        perform_task(options['scenario_id'],
                     options['tasktype_id'],
                     options['worker_nr'])

