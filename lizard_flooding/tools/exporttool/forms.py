from django import forms
from lizard_flooding.tools.exporttool.models import ExportRun

class ExportRunForm(forms.ModelForm):
    class Meta:
        model = ExportRun
        fields = ('name', 'description', 'gridsize')
