from django.core.management.base import BaseCommand

from flooding_lib import models
from flooding_lib import excel_import_export
from django.utils.translation import activate


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        activate("nl")  # Nederlands

        for project in models.Project.objects.filter(pk=3).all():
            filename = excel_import_export.filename_for_project(project)
            excel_import_export.create_excel_file(project, filename)
