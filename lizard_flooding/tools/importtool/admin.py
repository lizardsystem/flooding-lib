#alphabetical order
from lizard.flooding.tools.importtool.models import ImportScenario, ImportScenarioInputField, InputField
    

from django.contrib import admin
from django.contrib import databrowse
from django.contrib.gis.admin import OSMGeoAdmin

'''
class PresentationLayerInline(admin.TabularInline):   
    model = Scenario_PresentationLayer
    extra = 2

class PresentationTypeInline(admin.TabularInline):   
    model = ResultType_PresentationType
    extra = 2
'''

class ImportScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'owner', 'validation_remarks' ]
    list_filter = ('state', 'owner',  )
    search_fields = ['name', ]

class InputFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'header', 'position', 'type', 'visibility_dependency_field', 'visibility_dependency_value', 'required'  ]
    list_filter = ('header', 'type', 'required'  )
    search_fields = ['name', ]


#alphabetical order
admin.site.register(ImportScenario, ImportScenarioAdmin)
admin.site.register(ImportScenarioInputField)
admin.site.register(InputField,InputFieldAdmin)
