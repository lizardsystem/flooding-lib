# -*- coding: utf-8 -*-
from flooding_presentation.models import Animation, Classified, \
    ClassifiedNr, CustomIndicator, Derivative, Field, FieldChoice, \
    PresentationGrid, PresentationLayer, PresentationNoGeom, \
    PresentationShape, PresentationSource, PresentationType, \
    PresentationValueTable, SupportLayers
from flooding_lib.models import Scenario_PresentationLayer
from flooding_lib.models import ResultType_PresentationType
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1


class FieldChoiceInline(admin.TabularInline):
    model = FieldChoice
    extra = 2


class SupportLayersInline(admin.StackedInline):
    model = SupportLayers
    #extra = 2


class ClassifiedNrInline(admin.TabularInline):
    model = ClassifiedNr
    extra = 2


class PresentationLayerInline(admin.TabularInline):
    model = Scenario_PresentationLayer
    extra = 1


class PresentationTypeInline(admin.TabularInline):
    model = ResultType_PresentationType
    extra = 1

#class FlowPresentationTypeInline(admin.TabularInline):
#    model = Flow_ResultType_PresentationType
#    extra = 1


class PresentationTypeInline(admin.TabularInline):
    model = ResultType_PresentationType
    extra = 1


class PresentationTypeAdmin(admin.ModelAdmin):

    list_display = (
        'name', 'active', 'custom_indicator', 'absolute', 'object',
        'parameter', 'geo_type', 'value_type', 'value_source_id_prefix',
        'generation_geo_source', 'generation_geo_source_part',
        'geo_source_filter', 'permission_level')
    inlines = [PresentationTypeInline, FieldInline, SupportLayersInline]


class CustomIndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)


class DerivativeAdmin(admin.ModelAdmin):
    list_display = (
        'dest_presentationtype', 'source_presentationtype',
        'combine_on', 'function_derivative',)


class FieldAdmin(admin.ModelAdmin):
    list_display = (
        'presentationtype', 'friendlyname', 'source_type',
        'is_main_value_field', 'name_in_source', 'field_type', )
    inlines = [FieldChoiceInline]


class PresentationLayerAdmin(admin.ModelAdmin):
    list_display = ('presentationtype', 'source_application', )
    inlines = [PresentationLayerInline]


class AnimationAdmin(admin.ModelAdmin):
    list_display = (
        'presentationlayer', 'firstnr', 'lastnr',
        'startnr', 'delta_timestep',)


class ClassifiedAdmin(admin.ModelAdmin):
    list_display = ('presentationlayer', 'firstnr', 'lastnr', )
    inlines = [ClassifiedNrInline]


class PresentationSourceAdmin(admin.ModelAdmin):
    list_display = ('type', 'file_location', 't_origin', 't_source',)


class PresentationGridAdmin(OSMGeoAdmin):
    list_display = (
        'id', 'presentationlayer', 'rownr', 'colnr', 'gridsize',
        'png_indexed_palette', 'png_default_legend', 'location_netcdf_file',)
    search_fields = ['id']
    ordering = ['png_indexed_palette']
    fieldsets = (
        (None, {
            'fields': ('extent', 'bbox_orignal_srid')
        }),
        ('bla', {
            'fields': ('gridsize', )
        })
        )


class PresentationShapeAdmin(admin.ModelAdmin):
    list_display = ('presentationlayer', 'geo_source', 'value_source',)


class PresentationNoGeomAdmin(admin.ModelAdmin):
    list_display = ('presentationlayer', 'value_source',)


class PresentationValueTableAdmin(admin.ModelAdmin):
    list_display = ('presentationsource', 'location_id', 'time', 'value',)


admin.site.register(PresentationType, PresentationTypeAdmin)
admin.site.register(CustomIndicator, CustomIndicatorAdmin)
admin.site.register(Derivative, DerivativeAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(PresentationLayer, PresentationLayerAdmin)
admin.site.register(Animation, AnimationAdmin)
admin.site.register(Classified, ClassifiedAdmin)
admin.site.register(PresentationSource, PresentationSourceAdmin)
admin.site.register(PresentationGrid, PresentationGridAdmin)
admin.site.register(PresentationShape, PresentationShapeAdmin)
admin.site.register(PresentationNoGeom, PresentationNoGeomAdmin)
admin.site.register(PresentationValueTable, PresentationValueTableAdmin)
