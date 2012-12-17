from django.core.management.base import BaseCommand
from flooding_lib.tasks.threedi_nc_220 import process_threedi_nc


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Gridsize: 1000 and 1250 must be dividable by gridsize, minimum is 0.5
        # gridsize_divider: auto choose size depending on native size. value of 2 is good.
        # Both None: automatic setting.
        process_threedi_nc(
            args[0], 'scenario_id',
            detailed=True, with_region=False, gridsize=None, gridsize_divider=None)
        # process_threedi_nc(
        #     args[0], 'scenario_id',
        #     detailed=True, with_region=False, gridsize=0.5)
