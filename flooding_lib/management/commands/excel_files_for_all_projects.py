"""Helper command to generate Excel files, for testing. Not for production use."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os

from django.core.management.base import BaseCommand

from flooding_lib import models
from flooding_lib import excel_import_export
from django.utils.translation import activate


class Command(BaseCommand):
    """Command class."""
    def handle(self, *args, **kwargs):
        activate("nl")  # Nederlands

        for project in models.Project.objects.filter(pk=3).all():
            filename = os.path.join('/tmp', project.excel_filename())
            excel_import_export.create_excel_file(project, filename)
