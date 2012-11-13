from django.core.management.base import BaseCommand
from flooding_lib.tasks.threedi_nc_220 import process_threedi_nc


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        process_threedi_nc(args[0], 'threedi_calculation_id', detailed=True)
