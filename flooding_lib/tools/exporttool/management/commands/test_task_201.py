from django.core.management.base import BaseCommand

from flooding_lib.tasks import calculate_export_data


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print 'Running ExportRun with id %s...' % args[0]
        calculate_export_data.calculate_export_data(args[0])
