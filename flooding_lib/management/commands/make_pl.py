from django.core.management.base import BaseCommand

from flooding_lib.tasks import presentationlayer_generation


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            print "Usage: make_pl <scenario_id>"
            print (
                "Call the presentationlayer_generation task for the scenario.")
            return

        scenario_id = args[0]
        presentationlayer_generation.perform_presentation_generation(
            int(scenario_id), None)
