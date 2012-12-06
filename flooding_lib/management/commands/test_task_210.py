from django.core.management.base import BaseCommand
from flooding_lib.tasks.threedi_210 import run_threedi_task


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print "Starting 3Di using scenario_id %s..." % args[0]
        run_threedi_task(args[0], 'scenario_id')
