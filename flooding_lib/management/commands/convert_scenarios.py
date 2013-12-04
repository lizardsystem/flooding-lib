import glob
import os

from django.db.transaction import commit_on_success
from django.conf import settings
from django.core.management.base import BaseCommand

from flooding_presentation.models import PresentationType
from flooding_lib import models
from flooding_lib.tasks import pyramid_generation
from flooding_lib.tasks import presentationlayer_generation


def scenarios():
    # All ROR scenarios
    ROR = models.Project.objects.get(pk=99)

    for scenario in ROR.all_scenarios():
        yield scenario


def is_converted(scenario):
    return scenario.presentationlayer.filter(
        presentationtype__geo_type=PresentationType.GEO_TYPE_PYRAMID).exists()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        log = open("logfile.txt", "w")

        for scenario in (s for s in scenarios() if not is_converted(s)):
            try:
                with commit_on_success():
                    pyramid_generation.sobek(scenario.id, settings.TMP_DIR)
                    pyramid_generation.his_ssm(scenario.id, settings.TMP_DIR)
                    presentationlayer_generation(scenario.id, None)

                    # Remove old animation PNGs of the presentation layer
                    # A copy is still available in the results dir, if needed
                    pngdir = os.path.join(
                        settings.EXTERNAL_PRESENTATION_MOUNTED_DIR,
                        'flooding', 'scenario', str(scenario.id), 'fls')
                    files = glob.glob(
                        os.path.join(pngdir, "*.png")) + glob.glob(
                        os.path.join(pngdir, "*.pgw"))

                    for f in files:
                        os.remove(f)

            except Exception as e:
                log.write(
                    "{} stopped due to an exception: {}"
                    .format(scenario.id, e))
