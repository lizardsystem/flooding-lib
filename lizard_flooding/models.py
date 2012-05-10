# -*- coding: utf-8 -*-
import datetime
import os

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from treebeard.al_tree import AL_Node #Adjacent list implementation

from lizard_presentation.models import PresentationLayer, PresentationType
from lizard_visualization.models import ShapeDataLegend, ValueVisualizerMap
from lizard_flooding.tools.approvaltool.models import ApprovalObject
from django.db.models.signals import post_delete
from django.db.models.signals import post_save

#------------- helper functions ------------------
def convert_color_to_hex(color_tuple):
    """Converts a tuple (r, g, b) to hex representation of tuple #AABBCC """
    r, g, b = color_tuple
    return '#%02X%02X%02X'%(r,g,b)

#------------ the classes ---------------------
def get_attachment_path(instance, filename):
    """
    Method that functions as a callback method to set dynamically the path of
    the uploaded file of an attachment.
    """
    return 'attachments/' + str(instance.content_type) + '/' + str(instance.object_id) + '/' + filename

class Attachment(models.Model):
    """An attachment

    An attachment can be related to any object due to generic relations.

    """


    #Fields needed for generic relation
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    name = models.CharField(max_length=200, blank=False)
    remarks = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to = get_attachment_path, blank = True, null = True)
    uploaded_by = models.CharField(max_length = 200, blank = False)
    uploaded_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
        db_table = 'flooding_attachment'

    def __unicode__(self):
        return self.name

class SobekVersion(models.Model):
    """Sobek version"""
    class Meta:
        verbose_name = _('Sobek version')
        verbose_name_plural = _('Sobek versions')
    name = models.CharField(max_length=200)
    fileloc_startfile = models.CharField(max_length=200)

    '''
    #is waarschijnlijk niet nodig
    startfile = models.TextField()
    '''
    class Meta:
        db_table = 'flooding_sobekversion'

    def __unicode__(self):
        return self.name

class SobekModel(models.Model):
    """sobekmodel properties:

    - has a sobekversion
    - has a sobekmodeltype
    - is related to cutofflocation through cutofflocationsobekmodelsetting*
    - is related to 0 or more externalwater*
    - is related to 0 or more regions*
    - is related to 0 or more scenario's*

    """

    SOBEKMODELTYPE_CHOICES = (
        (1, _('canal')),
        (2, _('inundation')),
        )
    SOBEKMODELTYPE_CANAL = 1
    SOBEKMODELTYPE_INUNDATION = 2
    TYPE_DICT = {1: u'%s'%_('canal'),
                 2: u'%s'%_('inundation'),}
    sobekversion = models.ForeignKey(SobekVersion)
    sobekmodeltype = models.IntegerField(choices=SOBEKMODELTYPE_CHOICES)

    active = models.BooleanField(default=True)
    project_fileloc = models.CharField(max_length=200)
    model_case = models.IntegerField()
    model_version = models.CharField(max_length=20)
    model_srid = models.IntegerField()

    model_varname = models.CharField(max_length=40, null=True, blank=True)
    model_vardescription = models.CharField(max_length=200, null=True, blank=True)
    remarks = models.TextField(null=True)
    attachments = generic.GenericRelation(Attachment)

    embankment_damage_shape = models.CharField(max_length=200, null=True, blank=True)

    code = models.CharField(max_length=15, null=True, blank=True)

    def __unicode__(self):
        try:
            if self.sobekmodeltype == self.SOBEKMODELTYPE_CANAL:
                return 'extw. model, code: %s, project %s, case  %s, version: %s'%(self.code,
                                                    self.project_fileloc,
                                                    str(self.model_case),
                                                    self.model_version)

            else:
                return 'inund. model, code: %s, project %s, case  %s, version: %s'%(self.code,
                                                    self.project_fileloc,
                                                    str(self.model_case),
                                                    self.model_version)
        except Exception, e:
            return 'error: %s'%e


    class Meta:
        verbose_name = _('Sobek model')
        verbose_name_plural = _('Sobek models')
        db_table = 'flooding_sobekmodel'

    def __unicode__(self):
        return 'type: %s case: %d version: %s'%(self.TYPE_DICT[self.sobekmodeltype],
                                                self.model_case,
                                                self.model_version)

    def get_summary_str(self):
        """Return object summary in str, with markdown layout
        """
        summary = ''
        summary += '* %s: %s\n'%(_('type'), self.TYPE_DICT[self.sobekmodeltype])
        summary += '* %s: %d\n'%(_('case'), self.model_case)
        summary += '* %s: %s'%(_('version'), self.model_version)
        return summary

class CutoffLocation(models.Model):
    """cutofflocation properties:

    - is related to 0 or more externalwaters
    - is related to 0 or more regions
    - is related to 0 or more scenario's
    - is related to sobekmodel through cutofflocationsobekid

    """
    TYPE_CHOICES = (
        (1, _('lock')), #sluis
        (2, _('culvert')), #duiker
        (3, _('weir')), #stuw
        (4, _('bridge')), #brug
        (5, _('undefined')),
        (6, _('generic_internal')), #kan vanalles zijn, intern
        )

    CUTOFFLOCATION_TYPE_LOCK = 1
    CUTOFFLOCATION_TYPE_CULVERT = 2
    CUTOFFLOCATION_TYPE_WEIR = 3
    CUTOFFLOCATION_TYPE_BRIDGE = 4
    CUTOFFLOCATION_TYPE_UNDEFINED = 5
    CUTOFFLOCATION_TYPE_GENERIC_INTERNAL = 6

    name = models.CharField(max_length=200)
    bottomlevel = models.FloatField()
    width = models.FloatField()
    deftclose = models.FloatField(blank=True, null=True) #deltatime
    type = models.IntegerField(choices = TYPE_CHOICES)
    geom = models.PointField('node itself', srid=4326)

    sobekmodels = models.ManyToManyField(SobekModel, through='CutoffLocationSobekModelSetting')

    code = models.CharField(max_length=15, null=True)

    class Meta:
        verbose_name = _('Cutoff location')
        verbose_name_plural = _('Cutoff locations')
        db_table = 'flooding_cutofflocation'

    def __unicode__(self):
        return self.name

    def isinternal(self):
        """Returns if CutoffLocation is an internal cutoff location

        True if it is exclusively connected to region's,
        False if it is exclusively connected to external waters
        None else
        """
        ew = self.externalwater_set.all()
        r = self.region_set.all()
        if ew and not r:
            return False
        if r and not ew:
            return True
        return None

    def get_deftclose_seconds(self):
        return int(self.deftclose*86400)

class ExternalWater(models.Model):
    """externalwater properties:

    - is related to 0 or more sobek models
    - is related to 0 or more cutofflocations

    """
    TYPE_CHOICES = (
        (1,_('sea')),
        (2,_('lake')),
        (3,_('canal')),
        (4,_('internal_lake')),
        (5,_('internal_canal')),
        (6,_('river')),
        (7,_('unknown')),
        (8,_('lower_river')),
        )
    TYPE_SEA = 1
    TYPE_LAKE = 2
    TYPE_CANAL = 3
    TYPE_INTERNAL_LAKE = 4
    TYPE_INTERNAL_CANAL = 5
    TYPE_RIVER = 6
    TYPE_UNKNOWN = 7
    TYPE_LOWER_RIVER = 8

    name = models.CharField(max_length=200)

    sobekmodels = models.ManyToManyField(SobekModel, blank=True)
    cutofflocations = models.ManyToManyField(CutoffLocation, blank=True)

    type = models.IntegerField(choices=TYPE_CHOICES)
    area = models.IntegerField(blank=True, null=True)

    deftstorm = models.FloatField(blank=True, null=True) #deltatime
    deftpeak = models.FloatField(blank=True, null=True) #deltatime
    deftsim = models.FloatField() #deltatime

    minlevel = models.FloatField(default= -10)
    maxlevel = models.FloatField(default = 15)

    code = models.CharField(max_length=15, null=True)

    class Meta:
        verbose_name = _('External water')
        verbose_name_plural = _('External waters')
        db_table = 'flooding_externalwater'

    def __unicode__(self):
        return self.name

class Dike(models.Model):
    """dike properties:

    - for now, holds no extra information

    """
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = _('Dike')
        verbose_name_plural = _('Dikes')
        db_table = 'flooding_dike'

    def __unicode__(self):
        return self.name

class WaterlevelSet(models.Model):
    """waterlevelset properties:

    - represents a complete graph per element

    """
    WATERLEVELSETTYPE_CHOICES = (
        (1, _('undefined')),
        (2, _('tide')),
        (3, _('breach')),
        )
    WATERLEVELSETTYPE_UNDEFINED = 1
    WATERLEVELSETTYPE_TIDE = 2
    WATERLEVELSETTYPE_BREACH = 3
    name = models.CharField(max_length=200)
    type = models.IntegerField(choices=WATERLEVELSETTYPE_CHOICES)
    remarks = models.TextField(null=True, blank=True)

    code = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = _('Waterlevel set')
        verbose_name_plural = _('Waterlevel sets')
        db_table = 'flooding_waterlevelset'

    def __unicode__(self):
        return self.name

class Waterlevel(models.Model):
    """waterlevel properties:

    - represents 2d graphs with datetime and values, where each row is 1 waterlevel
    - belongs to a waterlevel set

    """
    time = models.FloatField() #interval
    value = models.FloatField()
    waterlevelset = models.ForeignKey(WaterlevelSet)

    class Meta:
        unique_together = (("waterlevelset", "time"),)
        verbose_name = _('Waterlevel')
        verbose_name_plural = _('Waterlevels')
        db_table = 'flooding_waterlevel'

    def __unicode__(self):
        return u'%s: %s, %f'%(self.waterlevelset.__unicode__(),
                              str(datetime.timedelta(self.time)), self.value)

class Map(models.Model):
    """Stores wms entries"""
    name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    index = models.IntegerField(default=100)

    url = models.CharField(max_length=200)
    layers = models.CharField(max_length=200) #layernames seperated with comma
    transparent = models.NullBooleanField(default=None)
    tiled = models.NullBooleanField(default=None)
    srs = models.CharField(max_length=50, default='EPSG:900913')

    class Meta:
        db_table = 'flooding_map'

    def __unicode__(self):
        return self.name


class Region(models.Model):
    """region properties:

    - is related to 1 or more regiongroups
    - is related to 1 or more sobekmodels
    - is related to 0 or more cutofflocations

    """
    name = models.CharField(max_length=200)
    longname = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    maps = models.ManyToManyField(Map, blank=True)
    sobekmodels = models.ManyToManyField(SobekModel, blank=True)
    cutofflocations = models.ManyToManyField(CutoffLocation, blank=True)

    normfrequency = models.IntegerField(null=True, blank=True)

    #GeoDjango specific
    geom = models.MultiPolygonField('Region Border', srid=4326)
    objects = models.GeoManager()
    path = models.CharField(max_length=200)

    code = models.CharField(max_length=20, null=True)
    dijkringnr = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        db_table = 'flooding_region'

    def __unicode__(self):
        if self.longname:
            return self.longname
        else:
            return self.name

class RegionSet(AL_Node):
    """regionset properties:

    - is a tree of nodes, representing hierarchy in regionsets
    - is related to 0 or more regions
    - is related to 0 or more projects
    note: nog niet alle velden onder de knie.. dit is een django-treebeard implementatie

    """
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', related_name='children_set',
                               null=True, db_index=True, blank=True)
    regions = models.ManyToManyField(Region, blank=True)
    node_order_by = ['name']

    class Meta:
        verbose_name = _('Region set')
        verbose_name_plural = _('Region sets')
        db_table = 'flooding_regionset'

    def get_all_regions(self, filter_active=True):
        """get all regions from all descendants.

        filter_active can be set to None, True or False. If True, it will
        only return the regions where the active flag is set to
        True. Same for False.
        """
        all_regions = {}
        for r in self.regions.all():
            if filter_active is None or r.active == filter_active:
                all_regions[r.id] = r
        for d in self.get_descendants():
            for r in d.regions.all():
                if filter_active is None or r.active == filter_active:
                    all_regions[r.id] = r
        return Region.objects.filter(id__in = all_regions.keys())

    @models.permalink
    def get_absolute_url(self):
        return ('node-view', ('al', str(self.id),))

    def __unicode__(self):
        return self.name

class Breach(models.Model):
    """breach properties:

    - connects external water to region (many to many)
    - belongs to a single dike
    - has a single default tide
    - is related to 0 or more breachsets
    - is related to 0 or more scenario's

    """
    name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)
    externalwater = models.ForeignKey(ExternalWater)
    region = models.ForeignKey(Region)

    active = models.BooleanField(default=True)

    dike = models.ForeignKey(Dike)
    defaulttide = models.ForeignKey(WaterlevelSet) #must be of correct type

    levelnormfrequency = models.FloatField()
    canalbottomlevel = models.FloatField(null=True, blank=True)
    groundlevel = models.FloatField()

    defrucritical = models.FloatField()
    defbaselevel = models.FloatField(null=True, blank=True)
    decheight = models.FloatField(null=True, blank=True)
    decheightbaselevel = models.FloatField(null=True, blank=True)

    sobekmodels = models.ManyToManyField(SobekModel, through='BreachSobekModel')

    internalnode = models.PointField('internal node',srid=4326)
    externalnode = models.PointField('external node',srid=4326)
    geom = models.PointField('node itself',srid=4326)

    code = models.CharField(max_length=20, null=True)

    objects = models.GeoManager()

    class Meta:
        verbose_name = _('Breach')
        verbose_name_plural = _('Breaches')
        db_table = 'flooding_breach'
        ordering = ["name"]


    def get_all_projects(self):
        """find out all projects that the current breach is part of"""
        all_regionsets = {}
        all_projects = {}
        #collect all regionsets
        for rs in self.region.regionset_set.all():
            all_regionsets[rs.id] = rs
            for rs_ancestor in rs.get_ancestors():
                all_regionsets[rs_ancestor.id] = rs_ancestor
        #find all projects that contain at least one of the regionsets
        for rs in all_regionsets.values():
            for p in rs.project_set.all():
                all_projects[p.id] = p
        return all_projects

    def __unicode__(self):
        return self.name

class BreachSobekModel(models.Model):
    """
    Koppeltabel tussen Breach en SobekModel. Op te vragen vanuit
    SobekBreach: je hebt dan Breach en SobekModel

    deze tabel dient NIET om sobekmodel en breach aan elkaar te
    koppelen, die koppeling wordt ergens anders gelegd.  hier worden
    extra eigenschappen van de koppeling bepaald (sobekid).

    """
    sobekmodel = models.ForeignKey(SobekModel)
    breach = models.ForeignKey(Breach)

    sobekid = models.CharField(max_length=200)

    class Meta:
        unique_together = (("sobekmodel", "breach"),)
        db_table = 'flooding_breachsobekmodel'

    def __unicode__(self):
        return "%s - %s: %s"%(self.sobekmodel.__unicode__(), self.breach.__unicode__(),
                              self.sobekid)


class CutoffLocationSet(models.Model):
    """breachset properties:

    - is related to 0 or more breaches

    """
    name = models.CharField(max_length=200)
    cutofflocations = models.ManyToManyField(CutoffLocation)

    class Meta:
        verbose_name = _('Cutoff location set')
        verbose_name_plural = _('Cutoff location sets')
        db_table = 'flooding_cutofflocationset'

    def __unicode__(self):
        return self.name

class Project(models.Model):
    """project properties:

    - is related to usergroup permissions
    - is related to regiongroups
    - is referred to by 0 or more scenario's

    """
    friendlyname = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User)
    attachments = generic.GenericRelation(Attachment)

    regionsets = models.ManyToManyField(RegionSet, blank=True)
    regions = models.ManyToManyField(Region, blank=True)

    code = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        ordering = ('friendlyname', 'name', 'owner', )
        db_table = 'flooding_project'

    #Project -> RegionSet (+) -> (RegionSet ->) Region(+) -> Breach
    def get_all_breaches(self):
        all_regions = {}
        all_breaches = {}
        #get all regions from all regionsets
        for rs in self.regionsets.all():
            for r in rs.get_all_regions():
                all_regions[r.id] = r
        for r in all_regions.values():
            for b in r.breach_set.all():
                all_breaches[b.id] = b
        return all_breaches.values()

    def count_scenarios(self):
        """returns number of scenarios attached to this project."""
        return len(self.scenario_set.all())

    def __unicode__(self):
        return self.friendlyname

    def get_absolute_url(self):
        return reverse("flooding_project_detail", kwargs={"object_id": self.id})

class UserPermission(models.Model):
    """userpermission

    - if a permission is in the user permission table AND
    in the projectgrouppermission, then the permission is granted for
    that (user,project,permission)
    """

    PERMISSION_SCENARIO_VIEW = 1
    PERMISSION_SCENARIO_ADD = 2
    PERMISSION_SCENARIO_ADD_IMPORT = 7
    PERMISSION_SCENARIO_EDIT = 3
    PERMISSION_SCENARIO_APPROVE = 4
    PERMISSION_SCENARIO_DELETE = 5
    PERMISSION_SCENARIO_EDIT_SIMPLE = 6
#    permissions below not in use.
#    PERMISSION_PROJECT_ADD = 11
#    PERMISSION_PROJECT_EDIT = 12
#    PERMISSION_PROJECT_DELETE = 13
#    PERMISSION_TASK_VIEW = 21
#    PERMISSION_TASK_ADD = 22
#    PERMISSION_TASK_EDIT = 23
#    PERMISSION_TASK_DELETE = 24
#    PERMISSION_IMPORT_ADD = 30
#    PERMISSION_IMPORT_APPROVE = 31
#    PERMISSION_IMPORT_TO_MAINDATABASE = 32
#    PERMISSION_EXPORT_ADD = 40
#    PERMISSION_EXPORT_VIEW = 41

    PERMISSION_CHOICES = (
        (PERMISSION_SCENARIO_VIEW, _('view_scenario')),
        (PERMISSION_SCENARIO_ADD, _('add_scenario_new_simulation')),
        (PERMISSION_SCENARIO_ADD_IMPORT, _('add_scenario_import')),
        (PERMISSION_SCENARIO_EDIT, _('edit_scenario')),
        (PERMISSION_SCENARIO_APPROVE, _('approve_scenario')),
        (PERMISSION_SCENARIO_DELETE, _('delete_scenario')),
        (PERMISSION_SCENARIO_EDIT_SIMPLE, _('edit_scenario_simple')),
#        (PERMISSION_PROJECT_ADD, _('add_project')),
#        (PERMISSION_PROJECT_EDIT, _('edit_project')),
#        (PERMISSION_PROJECT_DELETE, _('delete_project')),
#        (PERMISSION_TASK_VIEW, _('view_task')),
#        (PERMISSION_TASK_ADD, _('add_task')),
#        (PERMISSION_TASK_EDIT, _('edit_task')),
#        (PERMISSION_TASK_DELETE, _('delete_task')),
#        (PERMISSION_IMPORT_ADD, _('add import scenarios')),
#        (PERMISSION_IMPORT_APPROVE, _('approve Import scenarios')),
#        (PERMISSION_IMPORT_TO_MAINDATABASE, _('Import scenario to maindatabase')),
#        (PERMISSION_EXPORT_ADD, _('add export')),
#        (PERMISSION_EXPORT_VIEW, _('view exports')),
        )

    user = models.ForeignKey(User)
    permission = models.IntegerField(choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = (("user", "permission"),)
        verbose_name = _('User permission')
        verbose_name_plural = _('User permissions')
        db_table = 'flooding_userpermission'

    def __unicode__(self):
        return u'%s: %s'%(self.user.__unicode__(),
                          self.get_permission_display())

class ProjectGroupPermission(models.Model):
    """grouppermission properties:

    - links a group to a project, through a permission

    """
    group = models.ForeignKey(Group)
    project = models.ForeignKey(Project)
    permission = models.IntegerField(choices=UserPermission.PERMISSION_CHOICES)

    class Meta:
        unique_together = (("group", "project", "permission"),)
        verbose_name = _('Project group permission')
        verbose_name_plural = _('Project group permissions')
        db_table = 'flooding_projectgrouppermission'

    def __unicode__(self):
        return u'%s - %s (%s)'%(self.group.__unicode__(),
                                self.project.__unicode__(),
                                self.get_permission_display())

class PermissionProjectShapeDataLegend(models.Model):
    """View permissions for visualization.models.ShapeDataLegend
    """
    project = models.ForeignKey(Project)
    shapedatalegend = models.ForeignKey(ShapeDataLegend)

    class meta:
        verbose_name = _('Permission project shapedatalegend')
        verbose_name_plural = _('Permissions project shapedatalegend')
        db_table = 'flooding_permissionprojectshapedatalegend'

    def __unicode__(self):
        return u'view %s - %s'%(self.project.__unicode__(), self.shapedatalegend.__unicode__())

class PermissionProjectGridDataLegend(models.Model):
    """View permissions for visualization.models.ValueVisualizerMap
    """
    project = models.ForeignKey(Project)
    griddatalegend = models.ForeignKey(ValueVisualizerMap)

    class meta:
        verbose_name = _('Permission project griddatalegend')
        verbose_name_plural = _('Permissions project griddatalegend')
        db_table = 'flooding_permissinoprojectgriddatalegend'

    def __unicode__(self):
        return u'view %s - %s'%(self.project.__unicode__(), self.griddatalegend.__unicode__())


class ExtraInfoField(models.Model):
    """extra informatie velden voor scenarios
    """

    # New headers added 20120510
    HEADER_SCENARIO = 1
    HEADER_LOCATION = 2
    HEADER_MODEL = 4
    HEADER_OTHER = 5
    HEADER_FILES = 6

    HEADER_GENERAL = 10
    HEADER_METADATA = 20
    HEADER_BREACH = 30
    HEADER_EXTERNALWATER = 40
    HEADER_NONE = 70

    HEADER_CHOICES = (
        (HEADER_SCENARIO, _('scenario')),
        (HEADER_LOCATION, _('location')),
        (HEADER_MODEL, _('model')),
        (HEADER_OTHER, _('other')),
        (HEADER_FILES, _('files')),
        (HEADER_GENERAL, _('general')),
        (HEADER_METADATA, _('metadata')),
        (HEADER_BREACH, _('breaches')),
        (HEADER_EXTERNALWATER, _('externalwater')),
        (HEADER_NONE, _('none')),
    )

    name = models.CharField(max_length=200, unique = True)
    use_in_scenario_overview = models.BooleanField(default = False)
    header = models.IntegerField(choices=HEADER_CHOICES, default=HEADER_METADATA)
    position = models.IntegerField(default=0)

    class Meta:
        db_table = 'flooding_extrainfofield'

    def __unicode__(self):
        return self.name

class ExtraScenarioInfo(models.Model):
    """De extra metadata waarden van een scenario
    """
    extrainfofield = models.ForeignKey('ExtraInfoField')
    scenario = models.ForeignKey('Scenario')
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = (("extrainfofield", "scenario"),)
        db_table = 'flooding_extrascenarioinfo'

    def __unicode__(self):
        return self.scenario.__unicode__() + ', ' + self.extrainfofield.__unicode__() + ': ' + str(self.value)

class Scenario(models.Model):
    """scenario properties:

    - belongs to a single project
    - is related to 1 or more breaches
    - is related to 0 or more cutofflocations
    - is related to 1 or more sobekmodels
    - is referred to by tasks
    - is referred to by results

    """
    CALCPRIORITY_CHOICES = (
        (20, _('low')),
        (30, _('medium')),
        (40, _('high')),
        )
    CALCPRIORITY_LOW = 20
    CALCPRIORITY_MEDIUM = 30
    CALCPRIORITY_HIGH = 40

    STATUS_DELETED = 10
    STATUS_APPROVED = 20
    STATUS_DISAPPROVED = 30
    STATUS_CALCULATED = 40 #but not yet approved
    STATUS_ERROR = 50
    STATUS_WAITING = 60
    STATUS_NONE = 70

    STATUS_CHOICES = (
        (STATUS_DELETED, _('deleted')),
        (STATUS_APPROVED, _('approved')),
        (STATUS_DISAPPROVED, _('disapproved')),
        (STATUS_CALCULATED, _('calculated')),
        (STATUS_ERROR, _('error')),
        (STATUS_WAITING, _('waiting')),
        (STATUS_NONE, _('none')),
        )

    name = models.CharField(_('name'), max_length=200)
    owner = models.ForeignKey(User)
    remarks = models.TextField(_('remarks'), blank=True, null=True, default=None)
    project = models.ForeignKey(Project)
    attachments = generic.GenericRelation(Attachment)
    approvalobject = models.ForeignKey(ApprovalObject,blank=True, null=True, default=None)

    breaches = models.ManyToManyField(Breach, through='ScenarioBreach')
    cutofflocations = models.ManyToManyField(CutoffLocation,
                                             through='ScenarioCutoffLocation',
                                             blank=True) #optional
    strategy = models.ForeignKey('Strategy',blank=True, null=True, default=None)

    sobekmodel_inundation = models.ForeignKey(SobekModel)

    tsim = models.FloatField() #datetime object, time in days
    calcpriority = models.IntegerField(choices=CALCPRIORITY_CHOICES,
                                       default=CALCPRIORITY_LOW)

    status_cache = models.IntegerField(choices=STATUS_CHOICES, default=None, null=True)
    presentationlayer = models.ManyToManyField(PresentationLayer, through = 'Scenario_PresentationLayer')

    migrated = models.NullBooleanField(blank = True, null=True)

    code = models.CharField(max_length=15, null=True)

    workflow_template = models.ForeignKey(
        'lizard_flooding_worker.WorkflowTemplate',
        db_column='workflow_template')

    class Meta:
        ordering = ('name', 'project', 'owner', )
        verbose_name = _('Scenario')
        verbose_name_plural = _('Scenarios')
        db_table = 'flooding_scenario'

    def __unicode__(self):
        return self.name

    def get_tsim(self):
        return datetime.datetime(self.tsim)

    def get_rel_destdir(self):
        leading_breach = self.breaches.all()[0]
        return os.path.join(leading_breach.region.path, str(self.id))

    def get_status(self):
        """Get status of scenario by looking at tasks

        see:
        http://twiki.nelen-schuurmans.nl/cgi-bin/twiki/view/ITOntwikkeling/LizardFloodingDocumentatie
        todo: yet to be implemented
        """
        tasks = self.task_set.all().order_by('-tasktype','-tstart') #reverse order!
        if not(tasks):
            return self.STATUS_NONE

        for task in tasks:
            if task.tasktype.id == 200 and task.successful:
                return self.STATUS_DELETED
            elif task.tasktype.id == 190 and task.successful:
                return self.STATUS_APPROVED
            elif task.tasktype.id == 190 and task.successful == False:
                return self.STATUS_DISAPPROVED
            elif task.tasktype.id in [150,155,170,180,185] and task.successful:
                return self.STATUS_CALCULATED
            elif (task.tasktype.id in [120, 130, 150]) and task.tfinished is None and task.successful is None:
                return self.STATUS_ERROR
            elif task.tasktype.id == 50 and task.successful:
                return self.STATUS_WAITING
        return self.STATUS_NONE

    def get_status_str(self):
        return self.get_status_cache_display()

    def update_status(self):
        """
        Updates status_cache. Called by Task.save()
        """
        new_status = self.get_status()
        self.status_cache = new_status
        self.save()

    def get_absolute_url(self):
        return reverse('flooding_scenario_detail', kwargs={'object_id': self.pk})

class ScenarioBreach(models.Model):
    """scenario breach properties:

    - many to many table between Scenario and Breach
    - extra settings, such as waterlevel

    """
    METHOD_START_BREACH_CHOICES = (
        (1, _('at top')),
        (2, _('at moment x')),
        (3, _('at crossing level x')),
        (4, _('unknown/error at import')),
        )
    METHOD_START_BREACH_TOP = 1
    METHOD_START_BREACH_TIME = 2
    METHOD_START_BREACH_CROSS = 3

    scenario = models.ForeignKey(Scenario)
    breach = models.ForeignKey(Breach)
    waterlevelset = models.ForeignKey(WaterlevelSet)
    sobekmodel_externalwater = models.ForeignKey(SobekModel, null=True, blank=True)
    #bres
    widthbrinit = models.FloatField()
    methstartbreach = models.IntegerField(choices=METHOD_START_BREACH_CHOICES)
    tstartbreach = models.FloatField() #datetime.timedelta
    hstartbreach = models.FloatField()
    brdischcoef = models.FloatField()
    brf1 = models.FloatField()
    brf2 = models.FloatField()
    bottomlevelbreach = models.FloatField()
    ucritical = models.FloatField()
    pitdepth = models.FloatField()
    tmaxdepth = models.FloatField() #datetime.timedelta
    #waterlevels
    extwmaxlevel = models.FloatField()
    extwbaselevel = models.FloatField(null=True, blank=True, default=None)
    extwrepeattime = models.IntegerField(null=True, blank=True, default=None)
    tide = models.ForeignKey(WaterlevelSet, null=True, blank=True,
                             related_name='tide', default=None)
    tstorm = models.FloatField(null=True, blank=True, default=None)
    tpeak = models.FloatField(null=True, blank=True, default=None)
    tdeltaphase = models.FloatField(null=True, blank=True, default=None)
    manualwaterlevelinput = models.BooleanField(default=False)
    code = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        unique_together = (("scenario", "breach"),)
        verbose_name = _('Scenario breach')
        verbose_name_plural = _('Scenario breaches')
        db_table = 'flooding_scenariobreach'

    def __unicode__(self):
        return u'%s: %s (%s)'%(self.scenario.__unicode__(), self.breach.__unicode__(),
                               self.waterlevelset.__unicode__())

    def get_tstartbreach(self):
        """
        - Returns the tstartbreach as a timedelta (instead of a float)
        """
        return datetime.timedelta(self.tstartbreach)

    def get_tmaxdepth(self):
        """
        - Returns the tmaxdepth as a timedelta (instead of a float)
        """
        return datetime.timedelta(self.tmaxdepth)

    def get_summary_str(self):
        """Returns str summary of object, with markdown layout
        """
        sb_summary = ''
        sb_summary += '* %s: %s\n'%(('location'), self.breach)
        sb_summary += '* %s: %s\n'%(_('external water'), self.breach.externalwater)
        sb_summary += '* %s: %s\n'%(_('external water period'), self.extwrepeattime)
        sb_summary += '* %s: %s\n'%(_('external water max waterlevel'),self.extwmaxlevel)
        sb_summary += '* %s: %s\n'%(_('storm duration'), self.tstorm)
        sb_summary += '* %s: %s'%(_('pitdepth'), self.pitdepth)
        return sb_summary


class ScenarioCutoffLocation(models.Model):
    """scenario cutofflocation properties:

    - many to many table between Scenario and CutoffLocation
    - provides settings for scenario cutofflocation

    """
    scenario = models.ForeignKey(Scenario)
    cutofflocation = models.ForeignKey(CutoffLocation)
    action = models.IntegerField(null=True, blank=True, default=1) #1 = dicht, 2 = open
    tclose = models.FloatField() #interval timedelta // tclose can ook topen zijn, afhankelijk van action

    class Meta:
        unique_together = (("scenario", "cutofflocation"),)
        verbose_name = _('Scenario cutoff location')
        verbose_name_plural = _('Scenario cutoff locations')
        db_table = 'flooding_scenariocutofflocation'

    def __unicode__(self):
        return u'%s: %s'%(self.scenario.__unicode__(),
                          self.cutofflocation.__unicode__())

    def get_tclose(self):
        return datetime.timedelta(self.tclose)

    def get_tclose_seconds(self):
        """
        - Returns tclose as number of seconds
        """
        t = self.get_tclose()
        return t.seconds + t.days*24*60*60

class Program(models.Model):
    """Program meta info: Sobek, Ascii2Png, etc"""
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = _('Program')
        verbose_name_plural = _('Programs')
        db_table = 'flooding_program'

    def __unicode__(self):
        return self.name

class ResultType(models.Model):
    """Resulttype."""
    name = models.CharField(max_length=50)
    shortname_dutch = models.CharField(max_length=20, blank=True, null=True)
    overlaytype = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=15, blank=True, null=True)#mag weg
    color_mapping_name = models.CharField(max_length=256, blank=True, null=True)
    program = models.ForeignKey(Program)
    content_names_re = models.CharField(max_length=256, blank=True, null=True)
    presentationtype = models.ManyToManyField(PresentationType, through = 'ResultType_PresentationType')

    class Meta:
        verbose_name = _('Result type')
        verbose_name_plural = _('Result types')
        db_table = 'flooding_resulttype'

    def __unicode__(self):
        return self.shortname_dutch

class Result(models.Model):
    """result properties:
    better name is RawResult

    - belongs to a single scenario
    todo: types

    """
    scenario = models.ForeignKey(Scenario)
    resulttype = models.ForeignKey(ResultType)

    resultloc = models.CharField(max_length=200)
    deltat = models.FloatField( null=True, blank=True) #datetime.timedelta

    resultpngloc = models.CharField(max_length=200, null=True, blank=True)
    startnr = models.IntegerField(blank=True, null=True)#mag weg
    firstnr = models.IntegerField(blank=True, null=True)
    lastnr = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=10, blank=True, null=True)
    value = models.FloatField(null=True, blank=True)
    bbox = models.MultiPolygonField('Result Border', srid=4326, blank=True, null=True)

    class Meta:
        unique_together = (("scenario", "resulttype"),)
        verbose_name = _('Result')
        verbose_name_plural = _('Results')
        db_table = 'flooding_result'


class CutoffLocationSobekModelSetting(models.Model):
    """cutofflocationsobekmodelsettings properties:

    - many to many table between cutofflocation and sobekmodel
    - adds settings

    deze tabel dient NIET om sobekmodel en locationcutoff aan elkaar
    te koppelen, die koppeling wordt ergens anders gelegd.  hier
    worden extra eigenschappen van de koppeling bepaald.

    """


    cutofflocation = models.ForeignKey(CutoffLocation)
    sobekmodel = models.ForeignKey(SobekModel)

    sobekid = models.CharField(max_length=200)
    #todo: add settings

    class Meta:
        #unique_together = (("sobekmodel", "cutofflocation "),)
        verbose_name = _('Cutoff location sobek model setting')
        verbose_name_plural = _('Cutoff location sobek model settings')
        db_table = 'flooding_cutofflocationsobekmodelsetting'

    def __unicode__(self):
        return u'%s - %s: %s'%(self.sobekmodel.__unicode__(),
                               self.cutofflocation.__unicode__(),
                               self.sobekid)

class TaskType(models.Model):
    """tasktypes.

    id's of tasktypes are fixed! DO NOT CHANGE
    """

    TYPE_SCENARIO_CREATE = 50
    TYPE_SOBEK_PREPARATION = 120
    TYPE_SOBEK_CALCULATION = 130
    TYPE_SOBEK_PNG_CALCULATION = 150
    TYPE_HIS_SSM_CALCULATION = 160
    TYPE_HIS_SSM_PNG_CALCULATION = 180
    TYPE_SCENARIO_APPROVE = 190
    TYPE_SCENARIO_DELETE = 200

    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = _('Task type')
        verbose_name_plural = _('Task types')
        db_table = 'flooding_tasktype'

    def __unicode__(self):
        return u'%s (%d)'%(self.name, self.id)

class Task(models.Model):
    """task properties:

    - belongs to a single scenario
    tasktypes are fixed

    """
    #lookup for TaskType??

    scenario = models.ForeignKey(Scenario)
    remarks = models.TextField(blank=True)

    tasktype = models.ForeignKey(TaskType)
    creatorlog = models.CharField(max_length=40)
    tstart = models.DateTimeField()

    tfinished = models.DateTimeField(blank=True, null=True)
    errorlog = models.TextField(blank=True, null=True)
    successful = models.NullBooleanField(blank = True, null=True)

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        get_latest_by = 'tstart'
        db_table = 'flooding_task'

    def __unicode__(self):
        return u'Scenario %s (tasktype %d %s)'%(self.scenario.__unicode__(), self.tasktype.id, self.tasktype)

    def get_absolute_url(self):
        return reverse('flooding_task_detail', kwargs={'object_id': self.id})

    def save(self, **kwargs):
        """After saving, update scenario status"""
        super(Task, self).save(**kwargs)
        self.scenario.update_status()

    def delete(self):
        super(Task, self).delete()
        self.scenario.update_status()


# ZELFDE ALS TASKEXECUTOR??? KAN WEG???
#class TaskProcessor(models.Model):
#    """taskprocessor"""
#    class Meta:
#        verbose_name = _('Task processor')
#        verbose_name_plural = _('Task processors')
#    name = models.CharField(max_length=200)
#    ipaddress = models.IPAddressField()
#    port = models.PositiveIntegerField()
#
#    tasktypes = models.ManyToManyField(TaskType)
#
#    def __unicode__(self):
#        return self.name


class TaskExecutor(models.Model):
    """Defines all machines that can execute tasks"""
    name = models.CharField(max_length=200)
    ipaddress = models.IPAddressField()
    port = models.IntegerField()
    active = models.BooleanField(default=True)
    revision = models.CharField(max_length=20)
    seq = models.IntegerField(default=1)

    tasktypes = models.ManyToManyField(TaskType, null=True, blank=True)

    class Meta:
        verbose_name = _('Task executor')
        verbose_name_plural = _('Task executors')
        unique_together = (("ipaddress", "port"),("name", "seq"))
        db_table = 'flooding_taskexecutor'

    def __unicode__(self):
        return self.name

class Scenario_PresentationLayer(models.Model):
    """link to presentation.PresentationLayer """
    scenario = models.ForeignKey(Scenario)
    presentationlayer = models.ForeignKey(PresentationLayer)

    class Meta:
        db_table = 'flooding_scenario_presentationlayer'


class ResultType_PresentationType(models.Model):
    """link to presentation.PresentationType """
    resulttype = models.ForeignKey(ResultType)
    presentationtype = models.ForeignKey(PresentationType)
    remarks = models.CharField(max_length=100)

    class Meta:
        db_table = 'flooding_resulttype_presentationtype'

    def __unicode__(self):
        return self.remarks


class Strategy(models.Model):
    """
    Defines measures that can be taken to reach a certain goal.
    """

    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, blank=True, null=True)
    visible_for_loading =  models.BooleanField(default=False)
    user = models.ForeignKey(User, blank=True, null=True)
    save_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'flooding_strategy'
    def __unicode__(self):
        return self.name



class Measure(models.Model):
    """
    Defines a set of embankment-changements and new embankments
    that can be executed.
    """
    TYPE_UNKNOWN = 0
    TYPE_EXISTING_LEVEL = 1
    TYPE_SEA_LEVEL = 2

    ADJUSTMENT_TYPES = (
        (TYPE_UNKNOWN, _('unkown')),
        (TYPE_EXISTING_LEVEL, _('existing level')),
        (TYPE_SEA_LEVEL, _('new level')),
    )

    name = models.CharField(max_length=100)
    strategy = models.ManyToManyField(Strategy)
    reference_adjustment = models.IntegerField(choices=ADJUSTMENT_TYPES, default=TYPE_UNKNOWN)
    adjustment = models.FloatField(default=0)

    class Meta:
        db_table = 'flooding_measure'
    def __unicode__(self):
        return self.name

class EmbankmentUnit(models.Model):
    """
    Defines a unit of an embankment (e.g. if an embankment is
    splitted up in parts of 200 m).
    """
    TYPE_EXISTING = 0
    TYPE_NEW = 1

    EMBANKMENTUNIT_TYPES = (
        (TYPE_EXISTING, _('existing')),
        (TYPE_NEW, _('new')),
    )

    unit_id = models.CharField(max_length=20)
    type = models.IntegerField(choices=EMBANKMENTUNIT_TYPES)
    original_height = models.FloatField()
    region = models.ForeignKey(Region)
    measure = models.ManyToManyField(Measure)
    geometry = models.LineStringField()

    objects = models.GeoManager()


    class Meta:
        db_table = 'flooding_embankment_unit'
    def __unicode__(self):
        return self.unit_id

