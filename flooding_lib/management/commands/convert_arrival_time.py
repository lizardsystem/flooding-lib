import sys
import traceback

from django.core.management.base import BaseCommand

from flooding_presentation.models import PresentationType
from flooding_presentation.models import PresentationLayer
from flooding_lib import models
from flooding_lib.tasks import pyramid_generation


def convert_scenario(scenario):
    presentationtype_arrival_time = PresentationType.objects.get(
        resulttype__name='computed_arrival_time')

    try:
        # We need to re-convert the necessary animation results,
        # then convert the possibly generated arrivaltime result
        # and then make sure a presentationlayer exists.
        first_results = scenario.result_set.filter(
            resulttype__use_to_compute_arrival_times=True)
        for result in first_results:
            pyramid_generation.standalone_generation_for_result(result)

        arrival_time_results = scenario.result_set.filter(
            resulttype__name='computed_arrival_time')
        for result in arrival_time_results:
            pyramid_generation.standalone_generation_for_result(result)
            PresentationLayer.objects.get_or_create(
                scenario=result.scenario,
                presentationtype=presentationtype_arrival_time, defaults=dict(
                    source_application=2,
                    value=result.value))

        print("1: Converted successfully.")
    except Exception as e:
        print("0: {} stopped due to an exception: {}".format(scenario.id, e))
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb, 10)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            print "Usage: convert_arrival_time <scenario_id>"
            print ("Prints a status string, the first character is "
                   "0 or 1 indicating success.")
            return

        scenario_id = args[0]
        scenario = models.Scenario.objects.get(pk=scenario_id)

        convert_scenario(scenario)
