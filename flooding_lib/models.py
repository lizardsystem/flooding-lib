# -*- coding: utf-8 -*-
import datetime
import logging
import os

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from treebeard.al_tree import AL_Node  # Adjacent list implementation

from flooding_presentation.models import PresentationLayer, PresentationType
from flooding_lib.tools.approvaltool.models import ApprovalObject


logger = logging.getLogger(__name__)


#------------- helper functions ------------------
def convert_color_to_hex(color_tuple):
    """Converts a tuple (r, g, b) to hex representation of tuple #AABBCC """
    r, g, b = color_tuple
    return '#%02X%02X%02X' % (r, g, b)


#------------ the classes ---------------------
def get_attachment_path(instance, filename):
    """
    Method that functions as a callback method to set dynamically the path of
    the uploaded file of an attachment.
    """
    return ('attachments/' + str(instance.content_type) + '/' +
            str(instance.object_id) + '/' + filename)


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
    file = models.FileField(
        upload_to=get_attachment_path, blank=True, null=True)
    uploaded_by = models.CharField(max_length=200, blank=False)
    uploaded_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
        db_table = 'flooding_attachment'

    def __unicode__(self):
        return self.name

    @property
    def filename(self):
        return os.path.split(self.file.name)[1]


class SobekVersion(models.Model):
    """Sobek version"""
    class Meta:
        verbose_name = _('Sobek version')
        verbose_name_plural = _('Sobek versions')
        db_table = 'flooding_sobekversion'

    name = models.CharField(max_length=200)
    fileloc_startfile = models.CharField(max_length=200)

    '''
    #is waarschijnlijk niet nodig
    startfile = models.TextField()
    '''

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
    TYPE_DICT = {
        1: u'%s' % _('canal'),
        2: u'%s' % _('inundation'),
        }
    sobekversion = models.ForeignKey(SobekVersion)
    sobekmodeltype = models.IntegerField(choices=SOBEKMODELTYPE_CHOICES)

    active = models.BooleanField(default=True)
    project_fileloc = models.CharField(max_length=200)
    model_case = models.IntegerField()
    model_version = models.CharField(max_length=20)
    model_srid = models.IntegerField()

    model_varname = models.CharField(max_length=40, null=True, blank=True)
    model_vardescription = models.CharField(
        max_length=200, null=True, blank=True)
    remarks = models.TextField(null=True)
    attachments = generic.GenericRelation(Attachment)

    embankment_damage_shape = models.CharField(
        max_length=200, null=True, blank=True)

    code = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        verbose_name = _('Sobek model')
        verbose_name_plural = _('Sobek models')
        db_table = 'flooding_sobekmodel'

    def __unicode__(self):
        return ('type: %s case: %d version: %s' %
                (self.TYPE_DICT[self.sobekmodeltype],
                 self.model_case,
                 self.model_version))

    def get_summary_str(self):
        """Return object summary in str, with markdown layout
        """
        summary = ''
        summary += ('* %s: %s\n' %
                    (_('type'), self.TYPE_DICT[self.sobekmodeltype]))
        summary += ('* %s: %d\n' %
                    (_('case'), self.model_case))
        summary += ('* %s: %s' %
                    (_('version'), self.model_version))
        return summary


class CutoffLocation(models.Model):
    """cutofflocation properties:

    - is related to 0 or more externalwaters
    - is related to 0 or more regions
    - is related to 0 or more scenario's
    - is related to sobekmodel through cutofflocationsobekid

    """
    TYPE_CHOICES = (
        (1, _('lock')),     # sluis
        (2, _('culvert')),  # duiker
        (3, _('weir')),     # stuw
        (4, _('bridge')),   # brug
        (5, _('undefined')),
        (6, _('generic_internal')),  # kan vanalles zijn, intern
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
    deftclose = models.FloatField(blank=True, null=True)  # deltatime
    type = models.IntegerField(choices=TYPE_CHOICES)
    geom = models.PointField('node itself', srid=4326)

    sobekmodels = models.ManyToManyField(
        SobekModel, through='CutoffLocationSobekModelSetting')

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
        return int(self.deftclose * 86400)


class ExternalWater(models.Model):
    """externalwater properties:

    - is related to 0 or more sobek models
    - is related to 0 or more cutofflocations

    """
    TYPE_CHOICES = (
        (1, _('sea')),
        (2, _('lake')),
        (3, _('canal')),
        (4, _('internal_lake')),
        (5, _('internal_canal')),
        (6, _('river')),
        (7, _('unknown')),
        (8, _('lower_river')),
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

    deftstorm = models.FloatField(blank=True, null=True)  # deltatime
    deftpeak = models.FloatField(blank=True, null=True)   # deltatime
    deftsim = models.FloatField()  # deltatime

    minlevel = models.FloatField(default=-10)
    maxlevel = models.FloatField(default=15)

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

    - represents 2d graphs with datetime and values, where each row is
      1 waterlevel
    - belongs to a waterlevel set

    """
    time = models.FloatField()  # interval
    value = models.FloatField()
    waterlevelset = models.ForeignKey(WaterlevelSet)

    class Meta:
        unique_together = (("waterlevelset", "time"),)
        verbose_name = _('Waterlevel')
        verbose_name_plural = _('Waterlevels')
        db_table = 'flooding_waterlevel'

    def __unicode__(self):
        return (u'%s: %s, %f' %
                (self.waterlevelset.__unicode__(),
                 str(datetime.timedelta(self.time)), self.value))


class Map(models.Model):
    """Stores wms entries"""
    name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    index = models.IntegerField(default=100)

    url = models.CharField(max_length=200)
    layers = models.CharField(max_length=200)  # separated with comma
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

    note: nog niet alle velden onder de knie.. dit is een
    django-treebeard implementatie

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
        return Region.objects.filter(id__in=all_regions.keys())

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
    defaulttide = models.ForeignKey(WaterlevelSet)  # must be of correct type

    levelnormfrequency = models.FloatField()
    canalbottomlevel = models.FloatField(null=True, blank=True)
    groundlevel = models.FloatField()

    defrucritical = models.FloatField()
    defbaselevel = models.FloatField(null=True, blank=True)
    decheight = models.FloatField(null=True, blank=True)
    decheightbaselevel = models.FloatField(null=True, blank=True)

    sobekmodels = models.ManyToManyField(
        SobekModel, through='BreachSobekModel')

    internalnode = models.PointField('internal node', srid=4326)
    externalnode = models.PointField('external node', srid=4326)
    geom = models.PointField('node itself', srid=4326)

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
        return ("%s - %s: %s" %
                (self.sobekmodel.__unicode__(), self.breach.__unicode__(),
                 self.sobekid))


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

    color_mapping_name = models.CharField(
        max_length=256, blank=True, null=True)

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
        return self.scenarios.count()

    def __unicode__(self):
        return self.friendlyname

    def get_absolute_url(self):
        return reverse(
            "flooding_project_detail", kwargs={"object_id": self.id})

    def add_scenario(self, scenario):
        """Adds the scenario to this project. This is not the scenario's
        main project, the main project for the scenario must already be
        set and be different."""

        main_project = scenario.main_project
        if not main_project:
            raise ValueError(
                ("Tried to add scenario (pk={0}) to an extra project while it "
                 "doesn't have a main one yet.").format(scenario.pk))
        if main_project.pk == self.pk:
            raise ValueError(
                "Tried to add scenario (pk={0}) to its own main project."
                .format(scenario.pk))

        ScenarioProject.objects.get_or_create(
            project=self, scenario=scenario, is_main_project=False)

    @classmethod
    def in_scenario_list(cls, scenario_list):
        """Return a queryset of Projects that are related to scenarios
        in scenario_list."""
        return cls.objects.filter(scenarioproject__scenario__in=scenario_list)

    def all_scenarios(self):
        """Return a queryset of all scenarios attached to this project."""
        return self.scenarios.all()


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

    PERMISSION_CHOICES = (
        (PERMISSION_SCENARIO_VIEW, _('view_scenario')),
        (PERMISSION_SCENARIO_ADD, _('add_scenario_new_simulation')),
        (PERMISSION_SCENARIO_ADD_IMPORT, _('add_scenario_import')),
        (PERMISSION_SCENARIO_EDIT, _('edit_scenario')),
        (PERMISSION_SCENARIO_APPROVE, _('approve_scenario')),
        (PERMISSION_SCENARIO_DELETE, _('delete_scenario')),
        (PERMISSION_SCENARIO_EDIT_SIMPLE, _('edit_scenario_simple')),
        )

    user = models.ForeignKey(User)
    permission = models.IntegerField(choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = (("user", "permission"),)
        verbose_name = _('User permission')
        verbose_name_plural = _('User permissions')
        db_table = 'flooding_userpermission'

    def __unicode__(self):
        return (u'%s: %s' %
                (self.user.__unicode__(),
                 self.get_permission_display()))


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
        return (u'%s - %s (%s)' %
                (self.group.__unicode__(),
                 self.project.__unicode__(),
                 self.get_permission_display()))


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

    name = models.CharField(max_length=200, unique=True)
    use_in_scenario_overview = models.BooleanField(default=False)
    header = models.IntegerField(
        choices=HEADER_CHOICES, default=HEADER_METADATA)
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
        return (unicode(self.scenario) + ', ' +
                unicode(self.extrainfofield) + ': ' + str(self.value))

    @classmethod
    def get(cls, scenario, fieldname, scenario_overview_only=True):
        search = {
            'scenario': scenario,
            'extrainfofield__name': fieldname
            }
        if scenario_overview_only:
            search['extrainfofield__use_in_scenario_overview'] = True

        try:
            return cls.objects.get(**search)
        except cls.DoesNotExist:
            return None


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
    STATUS_CALCULATED = 40  # but not yet approved
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
    remarks = models.TextField(
        _('remarks'), blank=True, null=True, default=None)

    projects = models.ManyToManyField(
        Project, through='ScenarioProject', related_name='scenarios')
    attachments = generic.GenericRelation(Attachment)
    approvalobject = models.ForeignKey(
        ApprovalObject, blank=True, null=True, default=None)

    breaches = models.ManyToManyField(Breach, through='ScenarioBreach')
    cutofflocations = models.ManyToManyField(
        CutoffLocation, through='ScenarioCutoffLocation',
        blank=True)  # optional
    strategy = models.ForeignKey(
        'Strategy', blank=True, null=True, default=None)

    sobekmodel_inundation = models.ForeignKey(SobekModel, null=True)

    tsim = models.FloatField()  # datetime object, time in days
    calcpriority = models.IntegerField(choices=CALCPRIORITY_CHOICES,
                                       default=CALCPRIORITY_LOW)

    status_cache = models.IntegerField(
        choices=STATUS_CHOICES, default=None, null=True)
    presentationlayer = models.ManyToManyField(
        PresentationLayer, through='Scenario_PresentationLayer')

    migrated = models.NullBooleanField(blank=True, null=True)

    code = models.CharField(max_length=15, null=True)

    workflow_template = models.ForeignKey(
        'flooding_worker.WorkflowTemplate',
        db_column='workflow_template',
        null=True)

    # This field is ONLY here to support the old 'uitvoerder.py'
    # scripts that won't be updated to the new data model. It is set
    # by set_project and never changed.  Don't use this field
    # elsewhere.
    project_id = models.IntegerField(null=True)

    class Meta:
        ordering = ('name', 'owner', )
        verbose_name = _('Scenario')
        verbose_name_plural = _('Scenarios')
        db_table = 'flooding_scenario'

    def __unicode__(self):
        return self.name

    def set_project(self, project):
        """Set the MAIN project. Raises ValueError if it was already set."""
        if ScenarioProject.objects.filter(
            scenario=self, is_main_project=True).exists():
            raise ValueError(
                ("Tried to set_project on a scenario (pk={0}) "
                 "that already had one.")
                .format(self.pk))

        sp = ScenarioProject(
            project=project,
            scenario=self,
            is_main_project=True)
        sp.save()

        self.project_id = project.id
        self.save()

    @property
    def main_project(self):
        try:
            sp = ScenarioProject.objects.get(
                scenario=self, is_main_project=True)
            return sp.project
        except ScenarioProject.DoesNotExist:
            return None
        except ScenarioProject.MultipleObjectsReturned:
            logger.critical(
                ((u"SHOULD NOT HAPPEN: {0} ({1}).main_project "
                  "found multiple objects.")
                 .format(unicode(self)), self.pk))
            raise ValueError

    def approval_object(self, project):
        """Get the approval object relating to this scenario and that project,
        if any.

        Currently just returns self.approvalobject, but will be changed."""

        return self.approvalobject

    def set_approval_object(self, project, approval_object):
        """Set the approval object for this scenario in that project."""

        self.approvalobject = approval_object

    def get_tsim(self):
        return datetime.datetime(self.tsim)

    def get_rel_destdir(self):
        leading_breach = self.breaches.all()[0]
        return os.path.join(leading_breach.region.path, str(self.id))

    def get_status(self):
        """Get status of scenario by looking at tasks

        see:
        ITOntwikkeling/LizardFloodingDocumentatie on TWiki

        todo: yet to be implemented
        """
        tasks = (self.task_set.all().
                 order_by('-tasktype', '-tstart'))  # reverse order!
        if not(tasks):
            return self.STATUS_NONE

        for task in tasks:
            if task.is_type(TaskType.TYPE_SCENARIO_DELETE) and task.successful:
                return self.STATUS_DELETED
            elif (task.is_type(TaskType.TYPE_SCENARIO_APPROVE)
                  and task.successful):
                return self.STATUS_APPROVED
            elif (task.is_type(TaskType.TYPE_SCENARIO_APPROVE)
                  and task.successful == False):
                return self.STATUS_DISAPPROVED
            elif ((task.is_type(TaskType.TYPE_SOBEK_PNG_CALCULATION) or
                   task.is_type(TaskType.TYPE_HIS_SSM_CALCULATION) or
                   task.tasktype.id in [155, 170, 185])  # XXX
                  and task.successful):
                return self.STATUS_CALCULATED
            elif ((task.is_type(TaskType.TYPE_SOBEK_PREPARATION) or
                   task.is_type(TaskType.TYPE_SOBEK_CALCULATION) or
                   task.is_type(TaskType.TYPE_SOBEK_PNG_CALCULATION)) and
                  task.tfinished is None and
                  task.successful is None):
                return self.STATUS_ERROR
            elif (task.is_type(TaskType.TYPE_SCENARIO_CREATE)
                  and task.successful):
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
        return reverse('flooding_scenario_detail',
                       kwargs={'object_id': self.pk})

    def get_scenario_overview_extra_info(self, header):
        """Return a list of (fieldname, fieldvalue) tuples that should
        be should under this header in the scenario overview."""

        return [
            (field.extrainfofield.name, field.value)
            for field in self.extrascenarioinfo_set.filter(
                extrainfofield__header=header,
                extrainfofield__use_in_scenario_overview=True
                ).order_by('-extrainfofield__position')
            ]

    def get_attachment_list(self):
        """Return a list with information about this scenario's
        attachments, used to display them.

        There are four types of attachments: attached to the scenario,
        attached to the project, attached to the inundation model and
        attached to the external water model of this scenario.

        The list contains dictionaries, with key:

        - type: either 'scenario', 'project', 'inundationmodel' or
          'externalwatermodel'

        - description: a localized description of same

        - a list of Attachments
        """

        inundationmodel_attachments = (
            self.sobekmodel_inundation.attachments.
            order_by('-uploaded_date'))
        scenario_attachments = self.attachments.order_by('-uploaded_date')

        project_attachments = self.main_project.attachments.order_by(
            '-uploaded_date')

        # Get the the sobekmodels
        sobekmodel_choices = []
        for breach in self.breaches.all():
            for sobekmodel in breach.sobekmodels.all():
                sobekmodel_choices += [sobekmodel.id]
        breachmodel_attachments = Attachment.objects.filter(
            content_type=SobekModel,
            object_id__in=sobekmodel_choices
            ).order_by('-uploaded_date').all()

        attachment_list = [
            {'type': 'scenario',
             'description': _('Scenario attachments'),
             'attachments': scenario_attachments},
            {'project': 'project',
             'description': _('Project attachments'),
             'attachments': project_attachments},
            {'type': 'inundationmodel',
             'description': _('Inundation model attachments'),
             'attachments': inundationmodel_attachments},
            {'type': 'externalwatermodel',
             'description': _('External water model attachments'),
             'attachments': breachmodel_attachments}
            ]

        return attachment_list

    def all_projects(self):
        return self.projects.all()

    def create_calculated_status(self, username):
        """
        Used by importtool. Set up Tasks so that this scenario's state
        can be STATUS_CALCULATED.

        These tasks aren't functional. However, update_status() finds
        its status by looking at the tasks that have been successful
        for it.
        """
        Task.create_fake(
            scenario=self,
            task_type=TaskType.TYPE_SCENARIO_CREATE_AUTO,
            remarks="import scenario",
            creatorlog="uploaded by {0}".format(self.owner.get_full_name()))

        Task.create_fake(
            scenario=self,
            task_type=TaskType.TYPE_SOBEK_CALCULATION,
            remarks="import scenario",
            creatorlog="imported by {0}.".format(username))

        self.update_status()

    @classmethod
    def in_project_list(cls, project_list):
        """Return a Queryset of Scenarios that are related to the
        projects in the queryset project_list"""

        return cls.objects.filter(scenarioproject__project__in=project_list)


class ScenarioProject(models.Model):
    """Table implementing the ManyToMany relation between Scenario and Project.

    Model is needed because each scenario has one 'main' project and
    zero or more extra projects."""

    scenario = models.ForeignKey(Scenario)
    project = models.ForeignKey(Project)

    is_main_project = models.BooleanField(default=False)


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
    sobekmodel_externalwater = models.ForeignKey(
        SobekModel, null=True, blank=True)
    #bres
    widthbrinit = models.FloatField()
    methstartbreach = models.IntegerField(choices=METHOD_START_BREACH_CHOICES)
    tstartbreach = models.FloatField()  # datetime.timedelta
    hstartbreach = models.FloatField()
    brdischcoef = models.FloatField()
    brf1 = models.FloatField()
    brf2 = models.FloatField()
    bottomlevelbreach = models.FloatField()
    ucritical = models.FloatField()
    pitdepth = models.FloatField()
    tmaxdepth = models.FloatField()  # datetime.timedelta
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
        return (u'%s: %s (%s)' %
                (unicode(self.scenario), unicode(self.breach),
                 unicode(self.waterlevelset)))

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
        """Returns _UNICODE_ summary of object, with markdown layout
        """
        sb_summary = u''
        sb_summary += (u'* %s: %s\n' %
                       (('location'), self.breach))
        sb_summary += (u'* %s: %s\n' %
                       (_('external water'), self.breach.externalwater))
        sb_summary += (u'* %s: %s\n' %
                       (_('external water period'), self.extwrepeattime))
        sb_summary += (u'* %s: %s\n' %
                       (_('external water max waterlevel'), self.extwmaxlevel))
        sb_summary += (u'* %s: %s\n' %
                       (_('storm duration'), self.tstorm))
        sb_summary += (u'* %s: %s' %
                       (_('pitdepth'), self.pitdepth))
        return sb_summary


class ScenarioCutoffLocation(models.Model):
    """scenario cutofflocation properties:

    - many to many table between Scenario and CutoffLocation
    - provides settings for scenario cutofflocation

    """
    scenario = models.ForeignKey(Scenario)
    cutofflocation = models.ForeignKey(CutoffLocation)
    action = models.IntegerField(
        null=True, blank=True, default=1)  # 1 = dicht, 2 = open
    #interval timedelta // tclose can ook topen zijn, afhankelijk van action
    tclose = models.FloatField()

    class Meta:
        unique_together = (("scenario", "cutofflocation"),)
        verbose_name = _('Scenario cutoff location')
        verbose_name_plural = _('Scenario cutoff locations')
        db_table = 'flooding_scenariocutofflocation'

    def __unicode__(self):
        return (u'%s: %s' %
                (unicode(self.scenario), unicode(self.cutofflocation)))

    def get_tclose(self):
        return datetime.timedelta(self.tclose)

    def get_tclose_seconds(self):
        """
        - Returns tclose as number of seconds
        """
        t = self.get_tclose()
        return t.seconds + t.days * 24 * 60 * 60


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
    unit = models.CharField(max_length=15, blank=True, null=True)  # mag weg
    color_mapping_name = models.CharField(
        max_length=256, blank=True, null=True)
    program = models.ForeignKey(Program)
    content_names_re = models.CharField(max_length=256, blank=True, null=True)
    presentationtype = models.ManyToManyField(
        PresentationType, through='ResultType_PresentationType')

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
    deltat = models.FloatField(null=True, blank=True)  # datetime.timedelta

    resultpngloc = models.CharField(max_length=200, null=True, blank=True)
    startnr = models.IntegerField(blank=True, null=True)  # mag weg
    firstnr = models.IntegerField(blank=True, null=True)
    lastnr = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=10, blank=True, null=True)
    value = models.FloatField(null=True, blank=True)
    bbox = models.MultiPolygonField(
        'Result Border', srid=4326, blank=True, null=True)

    class Meta:
        unique_together = (("scenario", "resulttype"),)
        verbose_name = _('Result')
        verbose_name_plural = _('Results')
        db_table = 'flooding_result'


class CutoffLocationSobekModelSetting(models.Model):
    """cutofflocationsobekmodelsettings properties:

    - many to many table between cutofflocation and sobekmodel
    - adds settings

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
        return (u'%s - %s: %s' %
                (unicode(self.sobekmodel), unicode(self.cutofflocation),
                 self.sobekid))


class TaskType(models.Model):
    """tasktypes.

    id's of tasktypes are fixed! DO NOT CHANGE
    """

    TYPE_SCENARIO_CREATE = 50
    TYPE_SCENARIO_CREATE_AUTO = 60
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
        return u'%s (%d)' % (self.name, self.id)


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
    successful = models.NullBooleanField(blank=True, null=True)

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        get_latest_by = 'tstart'
        db_table = 'flooding_task'

    def __unicode__(self):
        return (u'Scenario %s (tasktype %d %s)' %
                (unicode(self.scenario), self.tasktype.id, self.tasktype))

    def get_absolute_url(self):
        return reverse('flooding_task_detail', kwargs={'object_id': self.id})

    def save(self, **kwargs):
        """After saving, update scenario status"""
        super(Task, self).save(**kwargs)
        self.scenario.update_status()

    def delete(self):
        super(Task, self).delete()
        self.scenario.update_status()

    def is_type(self, tasktype_id):
        """Check whether this Task's task type is equal to the given
        type ID."""
        return self.tasktype.id == tasktype_id

    @classmethod
    def create_fake(cls, scenario, task_type, remarks, creatorlog):
        """Create a 'fake' Task, one that is set to successful immediately."""
        cls.objects.create(
            scenario=scenario,
            tasktype=TaskType.objects.get(pk=task_type),
            remarks=remarks,
            creatorlog=creatorlog,
            tstart=datetime.datetime.now(),
            tfinished=datetime.datetime.now(),
            successful=True)


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
        unique_together = (("ipaddress", "port"), ("name", "seq"))
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
    visible_for_loading = models.BooleanField(default=False)
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
    reference_adjustment = models.IntegerField(
        choices=ADJUSTMENT_TYPES, default=TYPE_UNKNOWN)
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


class ScenarioShareOffer(models.Model):
    """Used when a scenario owner offers to share a scenario with
    another project."""
    scenario = models.ForeignKey(Scenario)
    new_project = models.ForeignKey(Project)

    class Meta:
        unique_together = ('original_project', 'new_project')


