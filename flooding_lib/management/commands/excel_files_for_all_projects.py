"""Helper command to generate Excel files. Called from cron."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from flooding_lib import models
from flooding_lib import excel_import_export
from django.utils.translation import activate


class Command(BaseCommand):
    """Command class."""
    def handle(self, *args, **kwargs):
        activate("nl")  # Nederlands

        for project in models.Project.objects.all():
            filename = os.path.join(
                settings.EXCEL_DIRECTORY,
                project.excel_filename())

            #print("Creating Excel for project {0}.".format(project.id))
            excel_import_export.create_excel_file(project, filename)
