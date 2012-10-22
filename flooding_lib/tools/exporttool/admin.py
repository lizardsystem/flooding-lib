#alphabetical order
from flooding_lib.tools.exporttool.models import ExportRun, Setting, Result
from django.contrib import admin
import os


class ResultAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_basename')
    actions = ['result_delete_with_file']

    def result_delete_with_file(self, request, queryset):
        try:
            export_folder = Setting.objects.get(key='EXPORT_FOLDER').value
        except:
            self.message_user(request, 'Er is iets mis met de Exporttool.Setting EXPORT_FOLDER. Niks gedaan.')
        messages = ['Resultaat objecten verwijderd (inclusief bestanden).']
        for result in queryset:
            try:
                os.remove(os.path.join(export_folder, result.file_basename))
            except OSError:
                messages.append('Bestand %s niet verwijderd.' % result.file_basename)
            result.delete()
        self.message_user(request, ' '.join(messages))
    result_delete_with_file.short_description = "Verwijder geselecteerde Resultaten inclusief resultaatbestand"


#alphabetical order
admin.site.register(ExportRun)
admin.site.register(Result, ResultAdmin)
admin.site.register(Setting)
