from django import forms
from django.utils.translation import ugettext_lazy as _
from lizard_flooding.models import Scenario, ScenarioCutoffLocation, ScenarioBreach, Project, Task


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        exclude = ('owner', 'breaches', 'cutofflocations',)

class ScenarioNameRemarksForm(forms.ModelForm):
    """Form to edit only the name and remarks of a scenario"""
    name = forms.CharField(label =_('Name'), widget=forms.TextInput(attrs={'class':'iwScenarioRemarks'}))
    remarks = forms.CharField(label = _('Remarks'), widget =forms.widgets.Textarea(attrs={'class':'iwScenarioRemarks'}) )

    class Meta:
        model = Scenario
        fields = ('name', 'remarks',)

class ScenarioCutoffLocationForm(forms.ModelForm):
    class Meta:
        model = ScenarioCutoffLocation
        exclude = ('scenario', )

class ScenarioBreachForm(forms.ModelForm):
    class Meta:
        model = ScenarioBreach
        exclude = ('scenario', )

class TaskApprovalForm(forms.ModelForm):
    remarks = forms.CharField(label  = _('Remarks'), widget = forms.widgets.Textarea(attrs={'class':'iwScenarioApproval'}) )
    successful = forms.CharField(label  = _('Successful'), widget=forms.NullBooleanSelect(attrs={'class':'iwScenarioApproval'}), required=False)

    class Meta:
        model = Task
        fields = ('successful', 'remarks',)

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ('owner',)

class AttachmentForm(forms.Form):
    name = forms.CharField(label = _('Name'), max_length=200)
    remarks = forms.CharField(label = _('Remarks'), widget =forms.widgets.Textarea(attrs={'rows':4, 'cols':60}) )
    file = forms.FileField(label = _('File') )

    def __init__(self, sobekmodel_choices, *args,**kwargs):
        forms.Form.__init__(self, *args,**kwargs)
        if sobekmodel_choices:
            self.fields.insert(0,'Sobekmodel',forms.CharField(label = _('Sobek model'), widget = forms.widgets.Select(choices = sobekmodel_choices)))

class EditScenarioPropertiesForm(forms.Form):
    animation_start = forms.IntegerField(label = _('Start animation'), min_value=0)

