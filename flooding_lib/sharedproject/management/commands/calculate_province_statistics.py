"""Helper command to generate Excel files. Called from cron."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.core.management.base import BaseCommand

from flooding_lib import models as libmodels
from flooding_lib.sharedproject import models as sharedmodels
from flooding_lib import scenario_sharing

"""For projects in ROR only"""


class Command(BaseCommand):
    """Command class."""
    def handle(self, *args, **kwargs):
        ROR = libmodels.Project.objects.get(pk=scenario_sharing.PROJECT_ROR)

        for scenario in libmodels.Scenario.objects.filter(
            scenarioproject__project=ROR,
            ror_province__isnull=True):
            try:
                scenario.ror_province = sharedmodels.Province.province_for(
                    scenario)
                scenario.save()
            except sharedmodels.Province.DoesNotExist:
                pass
            except sharedmodels.Owner.DoesNotExist:
                pass

        all_scenarios = list(libmodels.Scenario.objects.filter(
                scenarioproject__project=ROR)
                             .exclude(
                ror_province__isnull=True))

        for province in sharedmodels.Province.objects.all():
            province.statistics = None  # Recalculate
            province.scenario_stats(ROR, all_scenarios)

