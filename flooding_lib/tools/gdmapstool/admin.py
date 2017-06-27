#alphabetical order
from flooding_lib.tools.gdmapstool import models
from django.contrib import admin
import os


class GDMapInlineAdmin(admin.TabularInline):
    model = models.GDMap
    fields = ["name", "creation_date"]



class GDMapProjectAdmin(admin.ModelAdmin):
    inlines = [GDMapInlineAdmin]


admin.site.register(models.GDMapProject, GDMapProjectAdmin)
