from django.core.management.base import BaseCommand
from flooding_lib.tasks.threedi_210 import run_threedi_task


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print "Starting 3Di..."
        run_threedi_task(args[0], 'threedi_calculation_id')
