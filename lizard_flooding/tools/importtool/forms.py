from django import forms
from .models import ImportScenario, GroupImport
from ...models import Breach, Project, Scenario, SobekModel, SobekVersion

class ImportScenarioForm(forms.ModelForm):
    """
        niet meer in gebruik
    """
    class Meta:
        model = ImportScenario
        exclude = ('state', 'action_taker', 'creation_date', 'project', 'breach', 'validation_remarks')
    description = forms.CharField(widget = forms.widgets.Textarea(attrs={'rows':1, 'cols':60}) )
    coordinates_breach_location = forms.CharField(widget = forms.widgets.Textarea(attrs={'rows':1, 'cols':60}) )    
    remarks = forms.CharField(widget = forms.widgets.Textarea(attrs={'rows':1, 'cols':60}) )
                
class VerifyScenarioForm(forms.ModelForm):
    """
        niet meer in gebruik
    """
    class Meta:
        model = ImportScenario
        exclude = ('action_taker', 
                   'creation_date',
                   'animation_flooding_file',
                   'max_depth_maps_file',
                   'max_flow_maps_file',
                   'arrival_times_map_file',
                   'animation_flow_file')
        
    description = forms.CharField(widget = forms.widgets.Textarea(attrs={'rows':1, 'cols':60}))
    coordinates_breach_location = forms.CharField(widget = forms.widgets.Textarea(attrs={'rows':1, 'cols':60}) )
    
    empty_choice = [(None, '----------')]

    project_choices = empty_choice +  [(project.id, project.name) for project in Project.objects.all()]
    scenario_choices = empty_choice +  [(scenario.id, scenario.name) for scenario in Scenario.objects.all()]
    breach_choices = empty_choice +  [(breach.id, breach.name) for breach in Breach.objects.all()]
    sobek_model_choices = empty_choice +  [(sobek_model.id, sobek_model.sobekmodeltype) for sobek_model in SobekModel.objects.all()]
    sobek_version_choices = empty_choice +  [(sobek_version.id, sobek_version.name) for sobek_version in SobekVersion.objects.all()]

    project_select = forms.ChoiceField(choices=project_choices)
    scenario_select = forms.ChoiceField(choices=scenario_choices)
    breach_select = forms.ChoiceField(choices=breach_choices)
    sobek_model_select = forms.ChoiceField(choices=sobek_model_choices)
    sobek_version_select = forms.ChoiceField(choices=sobek_version_choices)
    
class GroupImportForm(forms.ModelForm):
    """
        import form for group imports
    """
    class Meta:
        model = GroupImport
        exclude = ('upload_successful')

class ImportScenarioFileUploadForm(forms.Form):
    """ The form for uploading files for an import scenario 
    
    """
    
    def __init__(self, filefields, *args,**kwargs):
        forms.Form.__init__(self, *args,**kwargs)   
        if filefields:            
            for f in filefields:
                if type(f) == type(u" "):            
                    self.fields.insert(0, f, forms.FileField(label = f, required=False, widget = forms.widgets.FileInput))
                else:
                    self.fields.insert(0, f.name, forms.FileField(label = f.name, required=False, widget = forms.widgets.FileInput(attrs={'size':'80'})))
