from django import forms
from .models import ExportRun

class ExportRunForm(forms.ModelForm):
    class Meta:
        model = ExportRun
        fields = ('name', 'description', 'gridsize')