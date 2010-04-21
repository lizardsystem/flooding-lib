#!/usr/bin/env python
from django.contrib import admin

from lizard_visualization.models import ShapeDataLegend
from lizard_visualization.models import ValueVisualizerMap
from lizard_visualization.models import ValueVisualizerMapFloatColor
from lizard_visualization.models import ValueVisualizerMapFloatFloat
from lizard_visualization.models import ValueVisualizerMapFloatInteger
from lizard_visualization.models import ValueVisualizerMapFloatSize
from lizard_visualization.models import ValueVisualizerMapFloatString
from lizard_visualization.models import ValueVisualizerMapStringString


class ValueVisualizerMapFloatColorInline(admin.TabularInline):
    model = ValueVisualizerMapFloatColor


class ValueVisualizerMapFloatSizeInline(admin.TabularInline):
    model = ValueVisualizerMapFloatSize


class ValueVisualizerMapFloatFloatInline(admin.TabularInline):
    model = ValueVisualizerMapFloatFloat


class ValueVisualizerMapFloatIntegerInline(admin.TabularInline):
    model = ValueVisualizerMapFloatInteger


class ValueVisualizerMapFloatStringInline(admin.TabularInline):
    model = ValueVisualizerMapFloatString


class ValueVisualizerMapStringStringInline(admin.TabularInline):
    model = ValueVisualizerMapStringString


class ValueVisualizerMapAdmin(admin.ModelAdmin):
    list_display = ('name', 'valuetype', 'interpolation', 'visualizertype',)
    list_filter = ('valuetype', 'visualizertype',)
    inlines = [ValueVisualizerMapFloatColorInline,
               ValueVisualizerMapFloatSizeInline,
               ValueVisualizerMapFloatFloatInline,
               ValueVisualizerMapFloatIntegerInline,
               ValueVisualizerMapFloatStringInline,
               ValueVisualizerMapStringStringInline,
               ]


class ShapeDataLegendAdmin(admin.ModelAdmin):
    list_display = ('name', 'presentationtype', 'color', 'size',
                    'symbol', 'rotation', 'shadowheight', )


admin.site.register(ValueVisualizerMap, ValueVisualizerMapAdmin)
admin.site.register(ValueVisualizerMapFloatColor)
admin.site.register(ValueVisualizerMapFloatSize)
admin.site.register(ValueVisualizerMapFloatFloat)
admin.site.register(ValueVisualizerMapFloatInteger)
admin.site.register(ValueVisualizerMapFloatString)
admin.site.register(ValueVisualizerMapStringString)
admin.site.register(ShapeDataLegend, ShapeDataLegendAdmin)
