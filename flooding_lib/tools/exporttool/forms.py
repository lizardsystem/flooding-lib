from django import forms
from flooding_lib.tools.exporttool.models import ExportRun


class ExportRunForm(forms.ModelForm):
    class Meta:
        model = ExportRun
        fields = ('name', 'description', 'gridsize')
