from django import forms
from flooding_lib.tools.gdmapstool.models import GDMap


class GDMapForm(forms.ModelForm):
    id =  forms.CharField(widget=forms.TextInput(attrs={'readonly':'True'}))
    class Meta:
        model = GDMap
        fields = ('id', 'name')
