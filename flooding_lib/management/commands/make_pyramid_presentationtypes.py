from django.core.management.base import BaseCommand

from flooding_presentation.models import PresentationType
from flooding_lib import models

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        for pt in PresentationType.objects.filter(
            geo_type=PresentationType.GEO_TYPE_GRID,
            value_type=PresentationType.VALUE_TYPE_VALUE):

            resulttypes = list(pt.resulttype_set.all())
            try:
                new_pt = PresentationType.objects.get(
                    name=pt.name[:31] + " (p)")
            except PresentationType.DoesNotExist:
                new_pt = pt
                # Save as new
                new_pt.id = None
                new_pt.name = pt.name[:31] + " (p)"
                new_pt.geo_type = pt.GEO_TYPE_PYRAMID
                new_pt.save()

            for resulttype in resulttypes:
                models.ResultType_PresentationType.objects.get_or_create(
                    resulttype=resulttype, presentationtype=new_pt,
                    defaults={'remarks': ''})

