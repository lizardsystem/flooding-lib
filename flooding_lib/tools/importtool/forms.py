from django import forms
from flooding_lib.tools.importtool.models import GroupImport
from flooding_lib.tools.importtool.models import RORKering


class GroupImportForm(forms.ModelForm):
    """import form for group imports"""
    class Meta:
        model = GroupImport
        exclude = ('upload_successful')


class ImportScenarioFileUploadForm(forms.Form):
    """The form for uploading files for an import scenario"""

    def __init__(self, filefields, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        if filefields:
            for f in filefields:
                if type(f) == type(u" "):
                    self.fields.insert(0, f, forms.FileField(
                            label=f, required=False,
                            widget=forms.widgets.FileInput))
                else:
                    self.fields.insert(0, f.name, forms.FileField(
                            label=f.name, required=False,
                            widget=forms.widgets.FileInput(
                                attrs={'size': '80'})))


class RORKeringForm(forms.ModelForm):
    """import form for group imports"""
    class Meta:
        model = RORKering
        exclude = ('upload_successful')
