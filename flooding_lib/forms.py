from django import forms
from django.utils.translation import ugettext_lazy as _

from flooding_lib.models import Scenario
from flooding_lib.models import ScenarioCutoffLocation
from flooding_lib.models import ScenarioBreach
from flooding_lib.models import Project
from flooding_lib.models import Task

# when not running in DEBUG mode, we need this to prevent an importerror
from flooding_lib.sharedproject.models import Province

class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        exclude = ('owner', 'breaches', 'cutofflocations', 'projects')


class ScenarioNameRemarksForm(forms.ModelForm):
    """Form to edit only the name and remarks of a scenario"""
    name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={'class': 'iwScenarioRemarks'}))
    remarks = forms.CharField(
        label=_('Remarks'),
        widget=forms.widgets.Textarea(attrs={'class': 'iwScenarioRemarks'}))

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
    remarks = forms.CharField(
        label=_('Remarks'),
        widget=forms.widgets.Textarea(attrs={'class': 'iwScenarioApproval'}))
    successful = forms.CharField(
        label=_('Successful'),
        widget=forms.NullBooleanSelect(attrs={'class': 'iwScenarioApproval'}),
        required=False)

    class Meta:
        model = Task
        fields = ('successful', 'remarks',)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ('owner',)


class AttachmentForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=200)
    remarks = forms.CharField(
        label=_('Remarks'),
        widget=forms.widgets.Textarea(attrs={'rows': 4, 'cols': 60}))
    file = forms.FileField(label=_('File'))

    def __init__(self, sobekmodel_choices, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        if sobekmodel_choices:
            self.fields.insert(
                0, 'Sobekmodel', forms.CharField(
                    label=_('Sobek model'),
                    widget=forms.widgets.Select(choices=sobekmodel_choices)))


class EditScenarioPropertiesForm(forms.Form):
    animation_start = forms.IntegerField(
        label=_('Start animation'), min_value=0)


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label=_('Upload the modified Excel file to update the scenarios'))


class ScenarioArchiveForm(forms.Form):
    
    scenarioid = forms.CharField(widget=forms.HiddenInput())
    action = forms.CharField(widget=forms.HiddenInput())
    can_edit = forms.CharField(widget=forms.HiddenInput(),
                               required=False)
    archived = forms.BooleanField(
        label=_('To archive'),
        required=False)
    archived_at = forms.DateField(
        label=_('Archived at'),
        required=False,
        widget=forms.widgets.TextInput(attrs={'readonly': 'True'}))
    archived_by = forms.CharField(
        label=_('Archived by'),
        required=False,
        widget=forms.widgets.TextInput(attrs={'readonly': 'True'}))

    def __init__(self, *args, **kwargs):
        self.action_value = kwargs['action']
        self.instance = kwargs['instance']
        self.can_edit = kwargs['can_edit']
        kwargs.pop('action')
        kwargs.pop('instance')
        kwargs.pop('can_edit')
        super(ScenarioArchiveForm, self).__init__(*args, **kwargs)
        self.set_initials()

    def set_initials(self):
        self.fields['scenarioid'].initial = self.instance.id
        self.fields['action'].initial = self.action_value
        self.fields['archived'].initial = self.instance.archived
        self.fields['archived_at'].initial = self.instance.archived_at
        self.fields['archived_by'].initial = self.instance.archived_by
        self.fields['can_edit'].initial = 'yes'
        if not self.can_edit:
            self.fields['archived'].widget.attrs['DISABLED'] = True
            self.fields['can_edit'].initial = 'no'

    def clean_scenarioid(self):
        return self.cleaned_data.get('scenarioid')

    def clean_archived(self):
        return self.cleaned_data.get('archived')
    
    def clean_archived_at(self):
        return self.cleaned_data.get('archived_at')

    def clean_archived_by(self):
        return self.cleaned_data.get('archived_by')
        
    
