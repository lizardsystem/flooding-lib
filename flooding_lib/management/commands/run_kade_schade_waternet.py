import csv
import os.path
from optparse import make_option
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from flooding_lib.models import Scenario
from flooding_lib.tasks.kadeschade_module_waternet import calc_damage

log = logging.getLogger("")

class Request(object):
    POST = {}


class Command(BaseCommand):
    help = ("Example: bin/django run_kade_schade_waternet scenario_id"
            "--log_level DEBUG")

    option_list = BaseCommand.option_list + (
            make_option('--log_level',
                        help='logging level 10=debug 50=critical',
                        default='DEBUG',
                        type='str'), )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No scenarios given.")

        numeric_level = getattr(logging, options["log_level"].upper(), None)
        if not isinstance(numeric_level, int):
            log.warning("Invalid log level: %s" % options["log_level"])
            numeric_level = 10

        log.setLevel(numeric_level)

        scenario_id = int(args[0])
        try:
            Scenario.objects.get(id=scenario_id)
        except Scenario.DoesNotExist:
            log.error("Scenario with id '{0}' does not exist".format(scenario_id))
            return

        success, message = calc_damage(scenario_id)

        if success:
            log.info("Task successfully completed")
        else:
            log.error("Task Failed with message: {0}".format(message))
