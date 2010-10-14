# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.contrib.gis.db import models


class PresentationType(models.Model):
    """ Definition of types that can be displayed by presentation module. """
    GEO_TYPE = (
        (1, _('grid')),
        (2, _('polygon')),
        (3, _('line')),
        (4, _('point')),
        (5, _('no geom')),
        )
    GEO_TYPE_GRID = 1
    GEO_TYPE_POLYGON = 2
    GEO_TYPE_LINE = 3
    GEO_TYPE_POINT = 4
    GEO_TYPE_NO_GEOM = 5

    VALUE_TYPE = (
        (1, _('only_geometry')),
        (2, _('value')),
        (3, _('time_serie')),
        (4, _('class_serie')),
        )
    VALUE_TYPE_ONLY_GEOMETRY = 1
    VALUE_TYPE_VALUE = 2
    VALUE_TYPE_TIME_SERIE = 3
    VALUE_TYPE_CLASS_SERIE = 4

    active = models.BooleanField(default = True)

    code = models.CharField(max_length=35)
    name = models.CharField(max_length=35)
    object = models.CharField(max_length=35)
    parameter = models.CharField(max_length=35)
    remarks = models.TextField(blank=True)
    custom_indicator = models.ForeignKey('CustomIndicator', null=True, blank=True) #for selecting subselection

    absolute = models.BooleanField(default = False)

    geo_type = models.IntegerField(choices = GEO_TYPE)#grid, location, value
    value_type = models.IntegerField(choices = VALUE_TYPE)#static, value, time_serie, class_serie,

    unit = models.CharField(max_length=20)
    class_unit = models.CharField(max_length=20, blank = True)
    value_source_parameter_name = models.CharField(max_length=30, blank = True)
    value_source_id_prefix = models.CharField(max_length=30, blank = True)

    generation_geo_source = models.CharField(max_length=30, blank = True)
    generation_geo_source_part = models.CharField(max_length=30, blank = True)
    geo_source_filter = models.CharField(max_length=80, blank = True)

    #numeric permission level; meaning is given by permission_manager
    permission_level = models.IntegerField(default=1)
    default_legend_id = models.IntegerField(blank = False)
    
    class Meta:        
        db_table = 'presentation_presentationtype'
        
    def __unicode__(self):
        return self.name



class CustomIndicator(models.Model):
    """ A label for a group of PresentationTypes """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    class Meta:        
        db_table = 'presentation_customindicator'
    
    def __unicode__(self):
        return self.name

class Derivative(models.Model):
    """ Information how to create a PresentionLayer based on another PresentaionLayer """

    COMBINE_TYPE = (
        (1, _('timeserie')),
        (2, _('locations')),
        (3, _('timeserie_locations')),
        (4, _('custom_comp_damage_embankments'))
        )
    COMBINE_TYPE_TIMESERIES = 1
    COMBINE_TYPE_LOCATIONS = 2
    COMBINE_TYPE_TIMESERIE_LOCATIONS = 3
    COMBINE_TYPE_CUSTOM_COMP_DAMAGE_EMBANKMENTS = 4

    FUNCTION_TYPE = (
        (1, _('min')),
        (2, _('max')),
        (3, _('mean')),
        (4, _('sum')),
        (5, _('sum_multiplied_by_dt')),
        )
    FUNCTION_TYPE_MIN = 1
    FUNCTION_TYPE_MAX = 2
    FUNCTION_TYPE_MEAN = 3
    FUNCTION_TYPE_SUM = 4
    FUNCTION_TYPE_SUM_MULTIPLIED_BY_DT = 5

    source_presentationtype = models.ForeignKey('PresentationType',related_name = 'source_presentationtype')
    dest_presentationtype = models.ForeignKey('PresentationType')
    combine_on = models.IntegerField(choices = COMBINE_TYPE) #
    function_derivative = models.IntegerField(choices = FUNCTION_TYPE)# # max, sum, sum_multiplied_by_dt, min, mean
    
    class Meta:        
        db_table = 'presentation_derivative'
    
class SupportLayers(models.Model):
    """ Information how to create a PresentionLayer based on another PresentaionLayer """

    presentationtype = models.OneToOneField('PresentationType',related_name = 'supported_presentationtype')
    supportive_presentationtype = models.ManyToManyField('PresentationType',related_name = 'supportive_presentationtypes')
    
    class Meta:        
        db_table = 'presentation_supportlayers'
    
class Field(models.Model):
    """ Fields of a PresentaionType """

    DATA_TYPE = (
        (1, _('float')),
        (2, _('integer')),
        (3, _('interval')),
        (4, _('datetime')),
        (5, _('string')),
        (6, _('choice')),
        )
    DATA_TYPE_FLOAT = 1
    DATA_TYPE_INTEGER = 2
    DATA_TYPE_INTERVAL = 3
    DATA_TYPE_DATETIME = 4
    DATA_TYPE_STRING = 5
    DATA_TYPE_CHOICE = 6

    SOURCE_TYPE = (
        (1, _('geo_source_col')),
        (2, _('value_source_param')),
    )
    SOURCE_TYPE_GEO_SOURCE_COL = 1
    SOURCE_TYPE_VALUE_SOURCE_PARAM = 2

    presentationtype = models.ForeignKey(PresentationType)
    friendlyname = models.CharField(max_length=50)
    source_type = models.IntegerField(choices = SOURCE_TYPE)
    is_main_value_field = models.BooleanField(default=False)
    name_in_source = models.CharField(max_length=80)
    field_type = models.IntegerField(choices = DATA_TYPE)
    
    class Meta:        
        db_table = 'presentation_field'

    def __unicode__(self):
        return self.presentationtype.name +': ' + self.friendlyname

class FieldChoice(models.Model):
    """ Possible choices of a Field """
    field = models.ForeignKey(Field)
    friendlyname = models.CharField(max_length=50)
    fieldname_source = models.CharField(max_length=80)
    
    class Meta:        
        db_table = 'presentation_fieldchoice'

    def __unicode__(self):
        return self.friendlyname

class PresentationLayer(models.Model):
    """Presentation layer - the root for all presentation stuff.
    """

    SOURCE_APPLICATION_CHOICES = (
        (1, _('None')),
        (2, _('Flooding')),
        )
    SOURCE_APPLICATION_DICT = dict(SOURCE_APPLICATION_CHOICES)

    SOURCE_APPLICATION_NONE = 1
    SOURCE_APPLICATION_FLOODING = 2

    presentationtype = models.ForeignKey(PresentationType)
    source_application = models.IntegerField(choices=SOURCE_APPLICATION_CHOICES, default=SOURCE_APPLICATION_NONE)
    value = models.FloatField(blank = True, null = True)
    
    class Meta:        
        db_table = 'presentation_presentationlayer'

    def __unicode__(self):
        return '%s - %s'%(self.presentationtype.__unicode__(),
                          self.SOURCE_APPLICATION_DICT[self.source_application])

class Animation(models.Model):
    """ Information about the PresentationLayer's timeserie of data """
    presentationlayer = models.OneToOneField(PresentationLayer, unique=True) #must be unique
    firstnr = models.IntegerField()
    lastnr = models.IntegerField()
    startnr = models.IntegerField(blank=True)
    delta_timestep = models.FloatField() #datetime object, time in days
    
    class Meta:        
        db_table = 'presentation_animation'

class Classified(models.Model):
    """ Information about the PresentationLayer's classes """
    presentationlayer = models.OneToOneField(PresentationLayer, unique=True) #must be unique
    firstnr = models.IntegerField()
    lastnr = models.IntegerField()
    
    class Meta:        
        db_table = 'presentation_classified'

class ClassifiedNr(models.Model):
    """ classes of a Classified PresentationLayer """
    classes = models.ForeignKey(Classified) #must be unique
    nr = models.IntegerField()
    boundary = models.FloatField()
    
    class Meta:        
        db_table = 'presentation_classifiednr'

class PresentationSource(models.Model):
    """ A data source for presentation """
    SOURCE_TYPE = (
        (1, _('value_table')),
        (2, _('shapefile')),
        (3, _('hisfile')),
        (4, _('zipped_hisfile')),
        (5, _('png_file')),
        (6, _('serie_png_files')),
        (7, _('png_file_indexed_pallette')),
        (8, _('serie_png_file_indexed_pallette')),
    )
    SOURCE_TYPE_VALUE_TABLE = 1
    SOURCE_TYPE_SHAPEFILE = 2
    SOURCE_TYPE_HISFILE = 3
    SOURCE_TYPE_ZIPPED_HISFILE = 4
    SOURCE_TYPE_PNG_FILE = 5
    SOURCE_TYPE_SERIE_PNG_FILES = 6
    SOURCE_TYPE_PNG_FILE_INDEXED_PALLETTE = 7
    SOURCE_TYPE_SERIE_PNG_FILE_INDEXED_PALLETTE = 8

    type = models.IntegerField(choices = SOURCE_TYPE)
    file_location = models.CharField(max_length=150,blank=True, null=True)
    t_source = models.DateTimeField(blank=True, null=True)
    t_origin = models.DateTimeField(blank=True, null=True)

    class Meta:        
        db_table = 'presentation_presentationsource'
    
    def __unicode__(self):
        return str(self.file_location)


class SourceLink(models.Model):
    ''' link between SourceLinkType and PresentationSource '''
    presentationsource = models.ManyToManyField(PresentationSource)
    sourcelinktype = models.ForeignKey('SourceLinkType')
    link_id = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    
    class Meta:        
        db_table = 'presentation_sourcelink'

class SourceLinkType(models.Model):
    ''' A label for a group of PresentationSources. Most of the time based on the origin of the data '''
    name = models.CharField(max_length=50)
    
    class Meta:        
        db_table = 'presentation_sourcelinktype'

class PresentationGrid(models.Model):
    ''' Information about a PresentationLayer of the type grid '''
    presentationlayer = models.OneToOneField(PresentationLayer, unique=True) #must be unique

    extent = models.MultiPolygonField('Result Border', srid=4326, blank = True, null = True)
    bbox_orignal_srid = models.IntegerField(blank = True, null = True)
    rownr = models.IntegerField()
    colnr = models.IntegerField()
    gridsize = models.IntegerField()
    png_indexed_palette = models.ForeignKey(PresentationSource, related_name = 'png_indexed_palette', null = True, blank = True)
    png_default_legend = models.ForeignKey(PresentationSource, related_name = 'png_default_legend',null = True, blank = True)
    location_netcdf_file = models.ForeignKey(PresentationSource, related_name = 'location_netcdf_file',null = True, blank = True)
    
    class Meta:        
        db_table = 'presentation_presentationgrid'

class PresentationShape(models.Model):
    ''' Information about a PresentationLayer of the type shape '''
    presentationlayer = models.OneToOneField(PresentationLayer, unique=True) #must be unique

    geo_source = models.ForeignKey(PresentationSource, related_name = 'geo_source', null = True, blank = True)
    value_source = models.ForeignKey(PresentationSource, related_name = 'value_source', null = True, blank = True)
    
    class Meta:        
        db_table = 'presentation_presentationshape'

class PresentationNoGeom(models.Model):
    ''' Information about a PresentationLayer of the type no geom '''
    presentationlayer = models.OneToOneField(PresentationLayer, unique=True) #must be unique
    value_source = models.ForeignKey(PresentationSource, null = True, blank = True)
    
    class Meta:        
        db_table = 'presentation_presentationnogeom'

class PresentationValueTable(models.Model):
    ''' table for storing values '''
    presentationsource = models.ForeignKey(PresentationSource, null = True)
    location_id = models.CharField(max_length=20, null = True, blank = True)
    parameter = models.CharField(max_length=20, null = True, blank = True,)
    time = models.FloatField(null = True, blank = True)
    value = models.FloatField()

    class Meta:        
        db_table = 'presentation_presentationvaluetable'
        
    def __unicode__(self):
        return str(self.presentationsource) + ' ' + str(self.location_id)