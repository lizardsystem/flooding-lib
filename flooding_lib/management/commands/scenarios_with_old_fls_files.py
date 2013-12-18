import os


from django.core.management.base import BaseCommand

from flooding_base.models import Setting
from flooding_lib import models
from flooding_lib.tasks import calculate_export_maps
from flooding_lib.util.flshinc import Flsh

from flooding_lib.management.commands.convert_scenarios import (
    Log, convert_scenario)


def scenarios():
    # All ROR scenarios
    ROR = models.Project.objects.get(pk=99)

    for scenario in ROR.all_scenarios():
        yield scenario


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        results_dir = (
            Setting.objects.get(
                key='DESTINATION_DIR').value.replace('\\', '/'))

        logger = Log()

        for scenario in scenarios():
            mwgeotransform = (
                calculate_export_maps.maxwaterdepth_geotransform(scenario))
            for result in scenario.result_set.all():
                if not result.resultloc:
                    continue
                result_location = os.path.join(
                    results_dir, result.resultloc.replace('\\', '/'))
                if not os.path.basename(result_location).startswith('fls'):
                    continue

                try:
                    fls = Flsh(result_location,
                               helper_geotransform=mwgeotransform)
                    needs_conversion = fls.uses_old_y0()
                except ValueError:
                    # Happens if there is more than one file in an fls.zip
                    continue

                if needs_conversion:
                    convert_scenario(scenario, logger)
