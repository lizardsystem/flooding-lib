#alphabetical order
from flooding_lib.tools.exporttool.models import ExportRun, Setting, Result
from django.contrib import admin
import os


class ResultAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_location')
    actions = ['result_delete_with_file']

    def result_delete_with_file(self, request, queryset):
        messages = ['Resultaat objecten verwijderd (inclusief bestanden).']
        for result in queryset:
            try:
                os.remove(result.file_location)
            except OSError:
                messages.append('Bestand %s niet verwijderd.' % result.file_location)
            result.delete()
        self.message_user(request, ' '.join(messages))
    result_delete_with_file.short_description = "Verwijder geselecteerde Resultaten inclusief resultaatbestand"


#alphabetical order
admin.site.register(ExportRun)
admin.site.register(Result, ResultAdmin)
admin.site.register(Setting)
