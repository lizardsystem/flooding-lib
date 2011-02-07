from django.core.management.base import BaseCommand
from django.conf import settings
#from lizard_netcdf.netcdf import NetcdfFolder

#from ijsselmeer.netcdf import NetcdfFile

class Command(BaseCommand):
    args = ''
    help = "Create geotiffs for all the netcdf files."

    def handle(self, *args, **options):
         """Find all netcdf files and generate a geotiff for them."""
        print 'gelukt'

