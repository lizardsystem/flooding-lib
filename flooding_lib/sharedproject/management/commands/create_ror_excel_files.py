"""Helper command to generate Excel files. Called from cron."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from flooding_lib import models
from flooding_lib.sharedproject import models as sharedmodels
from flooding_lib import excel_import_export
from django.utils.translation import activate

from flooding_lib.scenario_sharing import PROJECT_ROR


class Command(BaseCommand):
    """Command class."""
    def handle(self, *args, **kwargs):
        activate("nl")  # Nederlands

        ror = models.Project.objects.get(pk=PROJECT_ROR)

        for province in sharedmodels.Province.objects.all():
            filename = os.path.join(
                settings.EXCEL_DIRECTORY,
                "{0}.xls".format(province.name))

            scenarios = (scenario for scenario in
                         models.Scenario.objects.filter(
                    scenarioproject__project=ror)
                         if province.in_province(scenario))

            #print("Creating Excel for project {0}.".format(project.id))
            excel_import_export.create_excel_file(
                ror, scenarios, filename,
                include_approval=True)
