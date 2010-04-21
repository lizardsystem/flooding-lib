#alphabetical order
from .models import ExportRun, Setting, Result
from django.contrib import admin

#alphabetical order
admin.site.register(ExportRun)
admin.site.register(Result)
admin.site.register(Setting)