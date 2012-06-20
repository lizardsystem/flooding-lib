# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from flooding_presentation.models import Field, PresentationType


class ValueVisualizerMap(models.Model):
    """Maps a value from the source to a visualizable value (i.e. color, size)

    the sorted list of ValueVisualizerMapColor/Size/Value represent
    the mapping ranges
    """

    VALUETYPE_CHOICES = (
        (1, _('Absolute value')),
        (2, _('Percentage')),
        (3, _('Percentile')),
        )

    INTERPOLATION_CHOICES = (
        (1, _('No interpolation')),
        (2, _('Linear interpolation')),
        (3, _('Linear interpolation degrees')),
        )
    INTERPOLATION_NONE = 1
    INTERPOLATION_LINEAR = 2
    INTERPOLATION_LINEAR_DEGREES = 3

    VISUALIZERTYPE_CHOICES = (
        (1, _('float -> color')),
        (2, _('float -> size')),
        (3, _('float -> float')),
        (6, _('float -> integer')),
        (4, _('float -> string')),
        (5, _('string -> string')),
        )

    VISUALIZERTYPE_FLOAT_COLOR = 1
    VISUALIZERTYPE_FLOAT_SIZE = 2
    VISUALIZERTYPE_FLOAT_FLOAT = 3
    VISUALIZERTYPE_FLOAT_STRING = 4
    VISUALIZERTYPE_STRING_STRING = 5
    VISUALIZERTYPE_FLOAT_INTEGER = 6

    name = models.CharField(max_length=200)
    valuetype = models.IntegerField(choices=VALUETYPE_CHOICES)
    interpolation = models.IntegerField(choices=INTERPOLATION_CHOICES)
    visualizertype = models.IntegerField(choices=VISUALIZERTYPE_CHOICES)

    class Meta:
        db_table = 'visualization_valuevisualizermap'

    def __unicode__(self):
        return u'%s' % (self.name)

    def get_visualizer_set(self):
        """
        Looks at the visualizertype and return the queryset of the
        correct model corresponding to the type.

        If the visualizertype is invalid, return nothing
        """
        if self.visualizertype == self.VISUALIZERTYPE_FLOAT_COLOR:
            return self.valuevisualizermapfloatcolor_set
        elif self.visualizertype == self.VISUALIZERTYPE_FLOAT_SIZE:
            return self.valuevisualizermapfloatsize_set
        elif self.visualizertype == self.VISUALIZERTYPE_FLOAT_FLOAT:
            return self.valuevisualizermapfloatfloat_set
        elif self.visualizertype == self.VISUALIZERTYPE_FLOAT_STRING:
            return self.valuevisualizermapfloatstring_set
        elif self.visualizertype == self.VISUALIZERTYPE_STRING_STRING:
            return self.valuevisualizermapstringstring_set
        elif self.visualizertype == self.VISUALIZERTYPE_FLOAT_INTEGER:
            return self.valuevisualizermapfloatinteger_set

    def get_interpolated_value(self, input_value):
        """given inputvalue, calculate output value. currently only
        works for type=VISUALIZERTYPE_FLOAT_COLOR. If anything fails,
        return None
        """
        def get_interpolated_color_value(color1, color2, fraction):
            output_color = []
            for i in range(len(color1)):
                output_color.append(
                    color1[i] * (1 - fraction) + color2[i] * fraction)
            return tuple(output_color)

        output = None
        if self.visualizertype == self.VISUALIZERTYPE_FLOAT_COLOR:
            #self.valuevisualizermapfloatcolor_set.all() always has
            #value_in==None as first element
            if input_value is None:
                return self.valuevisualizermapfloatcolor_set.get(
                    value_in=None).get_value_out()
            if self.interpolation == self.INTERPOLATION_NONE:
                for color in self.valuevisualizermapfloatcolor_set.all():
                    if color.value_in is None:
                        output = color.get_value_out()
                    elif input_value <= color.value_in:
                        output = color.get_value_out()
                        break
            elif self.interpolation == self.INTERPOLATION_LINEAR:
                colors = list(
                    self.valuevisualizermapfloatcolor_set.exclude(
                        value_in=None))

                if len(colors) == 1:
                    output = colors[0].get_value_out()
                else:
                    if input_value <= colors[0].value_in:
                        output = colors[0].get_value_out()
                    elif input_value >= colors[-1].value_in:
                        output = colors[-1].get_value_out()
                    else:
                        for i in range(len(colors) - 1):
                            color1, color2 = colors[i], colors[i + 1]
                            if input_value >= color1.value_in and \
                                    input_value <= color2.value_in:
                                fraction = (input_value - color1.value_in) / \
                                    (color2.value_in - color1.value_in)
                                output = get_interpolated_color_value(
                                    color1.get_value_out(),
                                    color2.get_value_out(),
                                    fraction)
                                break
        return output


class ValueVisualizerMapFloatColor(models.Model):
    """float -> color mappings

    value_in=null is default
    r, g, b, a is in the range of 0..1
    """
    class Meta:
        ordering = ('value_in',)
        db_table = 'visualization_valuevisualizermapfloatcolor'

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.FloatField(blank=True, null=True)
    r = models.FloatField()
    g = models.FloatField()
    b = models.FloatField()
    a = models.FloatField()

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = str(self.value_in)
        return u'%s: %s -> (rgba) = (%1.2f %1.2f %1.2f %1.2f)' % (
            self.valuevisualizermap, value_in, self.r, self.g, self.b, self.a)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.r, self.g, self.b, self.a)

    def get_htmlcolor_out(self):
        """returns html color string of output value, i.e. '#556677' """
        return '#%02x%02x%02x' % (self.r * 255, self.g * 255, self.b * 255)


class ValueVisualizerMapFloatSize(models.Model):
    """float -> size mappings

    value_in=null is default
    x, y are in pixels
    """

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.FloatField(blank=True, null=True)
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        ordering = ('value_in',)
        db_table = 'visualization_valuevisualizermapfloatsize'

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = str(self.value_in)
        return u'%s: %s -> (x,y) = (%d,%d)' % (
            self.valuevisualizermap, value_in, self.x, self.y)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.x, self.y)


class ValueVisualizerMapFloatFloat(models.Model):
    """float -> float mappings (used for i.e. shadow height)

    value_in=null is default

    functions/properties that must be implemented: value_in, get_value_out()
    """

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.FloatField(blank=True, null=True)
    value_out = models.FloatField()

    class Meta:
        db_table = 'visualization_valuevisualizermapfloatfloat'

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = '%1.2f' % (self.value_in)
        return u'%s: %s -> %1.2f' % (self.valuevisualizermap, value_in,
                                     self.value_out)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.value_out,)


class ValueVisualizerMapFloatInteger(models.Model):
    """float -> integer mappings (used for i.e. shadow height)

    value_in=null is default

    functions/properties that must be implemented: value_in, get_value_out()
    """

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.FloatField(blank=True, null=True)
    value_out = models.IntegerField()

    class Meta:
        db_table = 'visualization_valuevisualizermapfloatinteger'

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = '%1.2f' % (self.value_in)
        return u'%s: %s -> %d' % (self.valuevisualizermap, value_in,
                                  self.value_out)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.value_out,)


class ValueVisualizerMapFloatString(models.Model):
    """float -> string mappings (used for i.e. shadow height)

    value_in=null is default
    """

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.FloatField(blank=True, null=True)
    value_out = models.CharField(max_length=200)

    class Meta:
        db_table = 'visualization_valuevisualizermapfloatstring'

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = '%1.2f' % (self.value_in)
        return u'%s: %s -> %s' % (self.valuevisualizermap, value_in,
                                  self.value_out)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.value_out,)


class ValueVisualizerMapStringString(models.Model):
    """string -> string value mappings (used for i.e. object classification)

    value_in=null is default
    """

    valuevisualizermap = models.ForeignKey(ValueVisualizerMap)
    value_in = models.CharField(max_length=200, blank=True, null=True)
    value_out = models.CharField(max_length=200)

    class Meta:
        db_table = 'visualization_valuevisualizermapstringstring'

    def __unicode__(self):
        if self.value_in is None:
            value_in = '(default)'
        else:
            value_in = str(self.value_in)
        return u'%s: %s -> %s' % (self.valuevisualizermap, value_in,
                                  self.value_out)

    def get_value_out(self):
        """returns a tuple representation of the valueout"""
        return (self.value_out,)


class ShapeDataLegend(models.Model):
    """Legend: maps all possible dimensions to ValueVisualizerMap entries

    can be applied to: point (all params), line (color), polygon
    (color), grid (color)

    todo: rename to Legend, because this model represents all possible Legends
    """
    name = models.CharField(max_length=200)
    presentationtype = models.ForeignKey(PresentationType,
                                         related_name='presentationtype_set',
                                         blank=False, null=False)

    color = models.ForeignKey(ValueVisualizerMap, related_name='color_set')
    color_field = models.ForeignKey(Field, related_name='color_field_set',
                                    blank=True, null=True)

    size = models.ForeignKey(ValueVisualizerMap, blank=True,
                             null=True, related_name='size_set')
    size_field = models.ForeignKey(Field, related_name='size_field_set',
                                   blank=True, null=True)

    symbol = models.ForeignKey(ValueVisualizerMap, blank=True,
                               null=True, related_name='symbol_set')
    symbol_field = models.ForeignKey(Field, related_name='symbol_field_set',
                                     blank=True, null=True)

    rotation = models.ForeignKey(ValueVisualizerMap, blank=True,
                                 null=True, related_name='rotation_set')
    rotation_field = models.ForeignKey(
        Field, related_name='rotation_field_set',
        blank=True, null=True)

    shadowheight = models.ForeignKey(
        ValueVisualizerMap, blank=True,
        null=True, related_name='shadowheight_set')
    shadowheight_field = models.ForeignKey(
        Field, related_name='shadowheight_field_set',
        blank=True, null=True)

    class Meta:
        db_table = 'visualization_shapedatalegend'

    def __unicode__(self):
        return u'%s' % (self.name)

    def get_palette(self, min_value, max_value):
        """Converts color to tuple of 768 items (256 colors, alpha is left out)

        input: self.color.valuevisualizermapcolor_set.all()
        """
        palette = []
        for i in range(256):
            input_val = min_value + (max_value - min_value) * i / 256.0
            color = self.color.get_interpolated_value(input_val)  # 4-tuple
            palette.extend(color[:3])

        return tuple(palette)
