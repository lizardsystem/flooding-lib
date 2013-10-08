from django import forms
from flooding_lib.tools.exporttool.models import ExportRun


class ExportRunForm(forms.ModelForm):

    class Meta:
        model = ExportRun
        fields = ('name',
                  'description',
                  'gridsize',
                  'export_max_waterdepth',
                  'export_max_flowvelocity',
                  'export_possibly_flooded',
                  'export_arrival_times',
                  'export_period_of_increasing_waterlevel',
                  'export_inundation_sources',
                  )
