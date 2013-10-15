# -*- coding: utf-8 -*-
"""Models for the flooding_lib app."""

import datetime
import logging
import operator
import os

from treebeard.al_tree import AL_Node  # Adjacent list implementation

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from flooding_base.models import Setting
from flooding_presentation.models import PresentationLayer, PresentationType
from flooding_lib.tools.approvaltool.models import ApprovalObject
from flooding_lib.tools.approvaltool.models import ApprovalObjectType
from flooding_lib import coordinates
from lizard_worker import models as workermodels
from lizard_worker import executor as workerexecutor

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
        return unicode(self.name)

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

    def __unicode__(self):
        return unicode(self.name)


class SobekModel(models.Model):
    """
    It is actual a Sobek Model, OR a 3Di model.

    3Di models have version '3di'

    sobekmodel properties:

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
    project_fileloc = models.CharField(
        max_length=200,
        help_text='In case of 3Di, point to model zipfile.')
    model_case = models.IntegerField()
    model_version = models.CharField(max_length=20)
    model_srid = models.IntegerField()

    model_varname = models.CharField(
        max_length=40, null=True, blank=True,
        help_text='In case of 3Di, .mdu filename in zip.')
    model_vardescription = models.CharField(
        max_length=200, null=True, blank=True)
    remarks = models.TextField(null=True)
    attachments = generic.GenericRelation(Attachment)

    embankment_damage_shape = models.CharField(
        max_length=200, null=True, blank=True)

    code = models.CharField(max_length=15, null=True, blank=True)
    keep_initial_level = models.BooleanField()

    class Meta:
        verbose_name = _('Sobek model')
        verbose_name_plural = _('Sobek models')
        db_table = 'flooding_sobekmodel'

    def is_3di(self):
        """Return True if this models is 3di."""
        return (
            self.sobekversion.name == "3di")

    def __unicode__(self):
        """More descriptive view for 3di models"""
        if self.is_3di():
            return ('3di model: %s %s' % (self.project_fileloc.split('/')[-1], self.model_varname))
        else:
            return ('type: %s case: %d version: %s' %
                    (self.TYPE_DICT[self.sobekmodeltype],
                     self.model_case,
                     self.model_version))

    def get_summary_str(self):
        """Return object summary in unicode, with markdown layout
        """
        summary = u''

        summary += (u'* %s: %s\n' %
                    (_('type'), self.TYPE_DICT[self.sobekmodeltype]))
        summary += (u'* %s: %d\n' %
                    (_('case'), self.model_case))
        summary += (u'* %s: %s' %
                    (_('version'), self.model_version))
        return summary


class ThreediModel(models.Model):
    """
    A 3Di model.

    It is essentially a folder with *.asc, optionally *.rgb, *.dat
    files. All referenced from the mdu file.
    """
    name = models.CharField(max_length=80)
    scenario_zip_filename = models.TextField(
        help_text='full path start with / or folder from Settings.SOURCE_DIR, must contain mdu file')
    mdu_filename = models.TextField(help_text='base filename of mdu file')

    def __unicode__(self):
        return self.name


class ThreediCalculation(models.Model):
    """
    An instance of a ThreediModel with own environment and variables.

    The 3Di calculation task gets a ThreediCalculation id as input.

    0) Create this model
    1) On local machine, copy ThreediModel zip
    2) Unpack zip into temp dir
    3) (TODO) alter .mdu and/or other files
    4) Do the math.
    """
    STATUS_CREATED = 1
    STATUS_NETCDF_CREATED = 2  # Task 210
    STATUS_IMAGES_CREATED = 3  # Task 220

    STATUS_CHOICES = (
        (STATUS_CREATED, 'created'),
        (STATUS_NETCDF_CREATED, 'netcdf created'),
        (STATUS_IMAGES_CREATED, 'images created, finished.'),
    )

    threedi_model = models.ForeignKey('ThreediModel')
    scenario = models.ForeignKey('Scenario')
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_CREATED)

    def __unicode__(self):
        return '%s - %s' % (self.threedi_model, self.scenario)

    @property
    def full_model_path(self):
        #/p-flod-fs-00-d1.external-nens.local/flod-share/Flooding/filedatabase/
        if self.threedi_model.scenario_zip_filename[0] == '/':
            return self.threedi_model.scenario_zip_filename  # = full path
        else:
            path = Setting.objects.get(key='SOURCE_DIR').value
            path = path.replace('\\', '/')  # Unix path
            model_path = os.path.join(path, self.threedi_model.scenario_zip_filename)
            return model_path

    @property
    def full_base_path(self):
        """This path contains all kinds of files depending on scenario"""
        return self.scenario.get_abs_destdir().replace('\\', '/')

    @property
    def full_result_path(self):
        """This path will contain "scenario.zip" and "subgrid_map.nc" after step 3 """
        return os.path.join(self.full_base_path, 'threedi')

    # def setup(self, remove_old_if_existing=False):
    #     """step 1)
    #     can delete destination if it exists, so use with caution
    #     """
    #     src = self.threedi_model.root_folder
    #     dst = self.model_path
    #     print 'Setup 3Di models: %s -> %s' % (src, dst)
    #     if os.path.exists(dst) and remove_old_if_existing:
    #         print 'Warning: removing old dir before creating new'
    #         os.removedirs(dst)
    #     print 'copying...'
    #     shutil.copytree(src, dst)

    # @property
    # def mdu_full_path(self):
    #     """Run setup first, then this file should be available"""
    #     return os.path.join(self.model_path, self.threedi_model.mdu_filename)


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
        return unicode(self.name)

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

    LIZ_TYPE_CHOICES = (
        (1, _('sea')),
        (2, 'estuarium'),
        (3, 'groot meer (incl. afgesloten zeearm)'),
        (4, 'grote rivier'),
        (5, 'scheepvaartkanaal'),
        (6, 'binnenmeer'),
        (7, 'regionale beek'),
        (8, 'regionale revier'),
        (9, 'boezemwater'),
        (10, 'polderwater'))

    name = models.CharField(max_length=200)

    sobekmodels = models.ManyToManyField(SobekModel, blank=True)
    cutofflocations = models.ManyToManyField(CutoffLocation, blank=True)

    type = models.IntegerField(choices=TYPE_CHOICES)
    liztype = models.IntegerField(choices=LIZ_TYPE_CHOICES,
                                  null=True, blank=True)
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
        return unicode(self.name)


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
        return unicode(self.name)


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
        return unicode(self.name)


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
                (unicode(self.waterlevelset),
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
        return unicode(self.name)


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

        Returns a list, ordered by name.
        """
        all_regions = set(
            region for region in self.regions.all()
            if filter_active is None or region.active == filter_active)

        for d in self.get_descendants():
            for region in d.regions.all():
                if filter_active is None or region.active == filter_active:
                    all_regions.add(region)

        return sorted(all_regions, key=operator.attrgetter('name'))

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
        """Options."""
        unique_together = (("sobekmodel", "breach"),)
        db_table = 'flooding_breachsobekmodel'

    def __unicode__(self):
        return u"{0} - {1}: {2}".format(
            self.sobekmodel, self.breach, self.sobekid)


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

    approval_object_type = models.ForeignKey(
        ApprovalObjectType,
        default=ApprovalObjectType.default_approval_type,
        null=True)  # Should never actually be null

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        ordering = ('friendlyname', 'name', 'owner', )
        db_table = 'flooding_project'

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

        scenarioproject, _ = ScenarioProject.objects.get_or_create(
            project=self, scenario=scenario, is_main_project=False)

        return scenarioproject

    @classmethod
    def in_scenario_list(cls, scenario_list):
        """Return a queryset of Projects that are related to scenarios
        in scenario_list."""
        return cls.objects.filter(scenarioproject__scenario__in=scenario_list)

    def all_scenarios(self):
        """Return a queryset of all scenarios attached to this project."""
        return self.scenarios.all()

    def original_scenarios(self):
        """Return a queryset of Scenarios that were originally in this project,
        not added to it later. Doesn't include deleted scenarios."""
        return Scenario.objects.filter(
            scenarioproject__project=self,
            scenarioproject__is_main_project=True).exclude(
            status_cache=Scenario.STATUS_DELETED)

    def excel_filename(self):
        """Return a valid unicode filename for an Excel file for this
        project."""
        name = self.name.encode('utf8').translate(None, """*<>[]=+"'/\\,.:;""")

        return b"{0} {1}.xls".format(self.id, name)

    def excel_generation_too_slow(self):
        """Does Excel generation for this project take too long?"""

        # If there is a file, use that...
        return os.path.exists(os.path.join(
                settings.EXCEL_DIRECTORY, self.excel_filename()))


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


def find_imported_value(fieldobject, data_objects):
    """Given an InputField object, find its values within the data_objects.

    InputFields know in what sort of objects they should be saved --
    in a Scenario, in a Breach, etc. We know in which objects all the
    information _was_ saved, the ones given in data_objects.

    Also some special hacks:

    - There are two InputFields that both store their info in Breach's
      geom field: x location and y location. So we handle that
      hardcoded here.

    - To make that worse, we also need to translate the stored WGS84
      coordinates to the RD we use for display.

    - Fields that store in 'Result' are ignored because we do them
      elsewhere.

    The result is returned.
    """

    #######
    # Import it here because doing so at the top of the file is a
    # cyclical import.
    #######
    from flooding_lib.tools.importtool.models import InputField

    value = None
    table = fieldobject.destination_table.lower()
    field = fieldobject.destination_field
    if table == 'extrascenarioinfo':
        info = ExtraScenarioInfo.get(
            scenario=data_objects['scenario'], fieldname=field)
        if info is not None:
            value = info.value

        if value is not None:
            value_type = fieldobject.type
            if value_type in (InputField.TYPE_INTEGER,):
                value = int(value)
            if value_type in (InputField.TYPE_SELECT,):
                try:
                    value = int(value)
                except ValueError:
                    pass  # Keep the string version of value
            elif value_type in (
                InputField.TYPE_FLOAT, InputField.TYPE_INTERVAL):
                value = float(value)
            elif value_type in (
                InputField.TYPE_STRING, InputField.TYPE_TEXT,
                InputField.TYPE_DATE):
                pass  # Already a string
            elif value_type in (InputField.TYPE_BOOLEAN,):
                # Value is a string like "1" or "0"
                value = bool(int(value))
            elif value_type in (InputField.TYPE_FILE,):
                # Don't know what to do
                value = None

    elif table in data_objects:
        value = getattr(data_objects[table], field, None)
        if table == 'breach' and field == 'geom':
            # Show in RD
            x, y = coordinates.wgs84_to_rd(
                value.x, value.y)

            if fieldobject.name.lower().startswith('x'):
                value = x
            if fieldobject.name.lower().startswith('y'):
                value = y
    elif table == 'result':
        # We do these differently
        pass
    else:
        # Unknown table, show it
        value = '{0}/{1}'.format(table, field)

    return value


class Scenario(models.Model):
    """scenario properties:

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
    STATUS_ARCHIVED = 80

    STATUS_CHOICES = (
        (STATUS_DELETED, _('deleted')),
        (STATUS_APPROVED, _('approved')),
        (STATUS_DISAPPROVED, _('disapproved')),
        (STATUS_CALCULATED, _('calculated')),
        (STATUS_ERROR, _('error')),
        (STATUS_WAITING, _('waiting')),
        (STATUS_NONE, _('none')),
        (STATUS_ARCHIVED, _('archived')),
    )

    name = models.CharField(_('name'), max_length=200)
    owner = models.ForeignKey(User)
    remarks = models.TextField(
        _('remarks'), blank=True, null=True, default=None)

    projects = models.ManyToManyField(
        Project, through='ScenarioProject', related_name='scenarios')
    attachments = generic.GenericRelation(Attachment)

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
        workermodels.WorkflowTemplate,
        db_column='workflow_template',
        null=True)

    # This field is ONLY here to support the old 'uitvoerder.py'
    # scripts that won't be updated to the new data model. It is set
    # by set_project and never changed.  Don't use this field
    # elsewhere.
    project_id = models.IntegerField(null=True)

    # Set by 'task 155' in the new flooding-worker tasks.
    has_sobek_presentation = models.NullBooleanField()

    #
    result_base_path = models.TextField(
        null=True, blank=True,
        help_text='If left blank, the path is retrieved through scenario.breaches[0].region.path'
    )
    # This field for 3di a setting
    config_3di = models.CharField(
        max_length=50, blank=True, null=True)

    # Used by the ROR Dashboard in the sharedproject subapp. Only
    # works as a cache to speed up those pages.
    ror_province = models.ForeignKey(
        'sharedproject.Province', null=True, blank=True)

    archived = models.BooleanField(default=False, verbose_name=_('Archived'))
    archived_at = models.DateTimeField(null=True, blank=True, 
                                       verbose_name=_('Archived at'))
    archived_by = models.ForeignKey(User, null=True, blank=True,
                                    related_name='archived_by_user',
                                    verbose_name=_('Archived by'))

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
            sp = ScenarioProject.objects.select_related(depth=1).get(
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

    def scenarioproject(self, project):
        return ScenarioProject.objects.select_related(
            depth=1).get(
            scenario=self, project=project)

    def approval_object(self, project):
        """Get the approval object relating to this scenario and that project,
        if any. Returns ScenarioProject.DoesNotExist if this scenario isn't in
        that project.

        If the relevant approvalobject doesn't exist yet, it will be created
        using the project's default approval object.

        Currently just returns self.approvalobject, but will be changed."""
        scenarioproject = self.scenarioproject(project)
        scenarioproject.ensure_has_approvalobject()

        return scenarioproject.approvalobject

    def visible_in_project(
        self, permission_manager, project,
        permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Does NOT check whether the user has rights to see this
        scenario at all, use the permission manager for that.

        This function decides whether, given that the user is allowed
        to see this scenario, it should be visible _in this
        project_."""

        # The permission manager makes sure we get only the scenarios
        # this user can see. However, because we want to show it in
        # more than one project sometimes, we have to do some extra
        # work to see _in which projects_ this user can see the
        # scenario so we only display it there.
        #
        # - If permission is other than SCENARIO_VIEW, no extra checks
        # - are needed.
        # - If the user has no approval rights, he can only see
        #   scenarios that are approved in that project.
        # - If the user has approval rights in some project, no
        #   approval checks are needed in that project.

        if permission != UserPermission.PERMISSION_SCENARIO_VIEW:
            return True

        if permission_manager.check_permission(
            UserPermission.PERMISSION_SCENARIO_APPROVE):
            if permission_manager.check_project_permission(
                project, UserPermission.PERMISSION_SCENARIO_APPROVE):
                return True

        return bool(self.scenarioproject(project).approved)

    def main_approval_object(self):
        """Return the approval object belonging to the main project."""
        try:
            return ApprovalObject.objects.get(
                scenarioproject__scenario=self,
                scenarioproject__is_main_project=True)
        except ApprovalObject.DoesNotExist:
            # Let approval_object() handle it
            return self.approval_object(self.main_project)

    def set_approval_object(self, project, approval_object):
        """Set the approval object for this scenario in that project.
        Raises ScenarioProject.DoesNotExist if this scenario isn't in
        that project."""

        scenarioproject = ScenarioProject.objects.get(
            scenario=self, project=project)
        scenarioproject.approvalobject = approval_object
        scenarioproject.save()

    def get_tsim(self):
        return datetime.datetime(self.tsim)

    def get_rel_destdir(self):
        if self.result_base_path:
            # 3Di way
            result_base_path = self.result_base_path
        else:
            # Traditional way
            leading_breach = self.breaches.all()[0]
            result_base_path = leading_breach.region.path
        return os.path.join(result_base_path, str(self.id))

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
            elif self.main_approval_object().approved:
                return self.STATUS_APPROVED
            elif self.main_approval_object().disapproved:
                return self.STATUS_DISAPPROVED

            # Flooding-worker tasks set this
            elif self.has_sobek_presentation:
                return self.STATUS_CALCULATED

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

    @property
    def is_approved(self):
        return self.status_cache == self.STATUS_APPROVED

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
            # Unicode, because get_full_name may contain non-ASCII!
            # And on general principle, of course
            creatorlog=u"uploaded by {0}".format(self.owner.get_full_name()))

        Task.create_fake(
            scenario=self,
            task_type=TaskType.TYPE_SOBEK_CALCULATION,
            remarks="import scenario",
            creatorlog=u"imported by {0}.".format(username))

        self.update_status()

    @classmethod
    def in_project_list(cls, project_list):
        """Return a Queryset of Scenarios that are related to the
        projects in the queryset project_list"""

        return cls.objects.filter(scenarioproject__project__in=project_list)

    def gather_data_objects(self):
        """Return various data objects related to this
        scenario. Cached."""
        if not hasattr(self, '_data_objects'):
            breaches = self.breaches.all()

            if not breaches:
                logger.critical(
                    "Scenario {0} has no breaches!!".format(self.id))
                return None

            breach = breaches[0]
            scenariobreach = self.scenariobreach_set.get(breach=breach)

            self._data_objects = {
                'scenario': self,
                'project': self.main_project,
                'scenariobreach': scenariobreach,
                'breach': breach,
                'externalwater': breach.externalwater,
                'region': breach.region
            }

        return self._data_objects

    def value_for_inputfield(self, inputfield):
        """Given an inputfield from the importtool, find where the
        value corresponding to it was stored and return it."""
        data_objects = self.gather_data_objects()

        if data_objects is not None:
            return find_imported_value(
                inputfield, self.gather_data_objects())

    def string_value_for_inputfield(self, inputfield):
        """Retrieve a value for inputfield from ExtraScenarioInfo model,
        if the value is an integer retrieve the value from InputField.
        """

        value = self.value_for_inputfield(inputfield)

        if isinstance(value, int):
            try:
                return inputfield.parsed_options[value]
            except:
                return value
        return value

    def set_value_for_inputfield(self, inputfield, value_object):
        """Given an inputfield and a value object, actually set that
        value on this scenario and save it."""
        table = inputfield.destination_table.lower()
        field = inputfield.destination_field

        if table not in ('scenario', 'scenariobreach', 'extrascenarioinfo'):
            raise NotImplementedError("Shouldn't happen.")

        if table == 'scenario':
            # Set it directly
            setattr(self, field, value_object.value)
            self.save()

        elif table == 'scenariobreach':
            scenariobreach = self.gather_data_objects()['scenariobreach']

            setattr(scenariobreach, field, value_object.value)
            scenariobreach.save()

        elif table == 'extrascenarioinfo':
            try:
                esi = ExtraScenarioInfo.objects.get(
                    scenario=self, extrainfofield__name=field)
            except ExtraScenarioInfo.DoesNotExist:
                eif = ExtraInfoField.objects.get(name=field)
                esi = ExtraScenarioInfo(
                    scenario=self,
                    extrainfofield=eif)
            esi.value = unicode(value_object)
            esi.save()

    def setup_initial_task(self, user):
        task = Task.objects.create(
            scenario=self,
            tasktype=TaskType.objects.get(pk=TaskType.TYPE_SCENARIO_CREATE),
            creatorlog=user.get_full_name(),
            tstart=datetime.datetime.now())

        if self.is_3di():
            workflow_template = workermodels.WorkflowTemplate.objects.get(
                code=workermodels.WorkflowTemplate.THREEDI_TEMPLATE_CODE)
        else:
            workflow_template = workermodels.WorkflowTemplate.objects.get(
                code=workermodels.WorkflowTemplate.DEFAULT_TEMPLATE_CODE)
        self.workflow_template = workflow_template
        self.save()
        workerexecutor.start_workflow(self.id, self.workflow_template.id)
        return task

    def has_values_for(self, inputfields):
        return all(
            self.value_for_inputfield(inputfield) is not None
            for inputfield in inputfields
            if (inputfield.required and not
                inputfield.ignore_in_scenario_excel_files))

    def setup_imported_task(self, username):
        self.create_calculated_status(username)
        workflow_template = workermodels.WorkflowTemplate.objects.get(
            code=workermodels.WorkflowTemplate.IMPORTED_TEMPLATE_CODE)
        self.workflow_template = workflow_template
        self.save()
        workerexecutor.start_workflow(self.id, self.workflow_template.id)

    def presentation_layer_of_type(self, type_id):
        pls = list(self.presentationlayer.filter(
                presentationtype__id=type_id))

        return pls[0] if pls else None

    def casualties(self):
        CASUALTIES_TYPE_ID = 20
        pl = self.presentation_layer_of_type(CASUALTIES_TYPE_ID)
        return int(pl.value) if pl else None

    def financial_damage(self):
        DAMAGE_AREA_TYPE_ID = 21
        pl = self.presentation_layer_of_type(DAMAGE_AREA_TYPE_ID)
        return pl.value if pl else None

    def get_result(
        self, resulttype=None, resulttype_id=None, shortname_dutch=None):
        """Find a result object using some information about the resulttype"""
        if not resulttype:
            if resulttype_id is not None:
                resulttype = ResultType.objects.get(pk=resulttype_id)
            else:
                resulttype = ResultType.objects.get(
                    shortname_dutch=shortname_dutch)

        try:
            return Result.objects.get(scenario=self, resulttype=resulttype)
        except Result.DoesNotExist:
            return Result(scenario=self, resulttype=resulttype)

    def get_abs_destdir(self):
        """
        The results destination dir.

        Used by 3Di stuff, task 210, 220.

        Destilled from presentationlayer_generation.py /
        calculaterisespeed_132.py
        """
        # Something like
        # \\servername\flod-share\Flooding\resultaten-staging
        dst_dir = Setting.objects.get(key='DESTINATION_DIR').value
        dst_dir.replace('\\', '/')  # Semi convert windows share name to unix name.
        # Plus something like "Dijkring xx/1234"
        output_dir_name = os.path.join(dst_dir, self.get_rel_destdir())
        return output_dir_name

    def is_3di(self):
        """Return True if this scenario uses 3di."""
        return (
            self.sobekmodel_inundation.sobekversion.name == "3di")


class ScenarioProject(models.Model):
    """Table implementing the ManyToMany relation between Scenario and Project.

    Model is needed because each scenario has one 'main' project and
    zero or more extra projects."""

    scenario = models.ForeignKey(Scenario)
    project = models.ForeignKey(Project)

    is_main_project = models.BooleanField(default=False)

    approvalobject = models.ForeignKey(
        ApprovalObject, blank=True, null=True, default=None)

    # Cache that is set by approvalobject. Values like ApprovalObject
    # approved and disapproved properties; if the scenario is neither
    # approved nor disapproved in this scenario, the value should be
    # None (null).
    approved = models.NullBooleanField(blank=True, null=True)

    def ensure_has_approvalobject(self):
        """Create an approvalobject for this scenario/project
        connection if there isn't one yet."""
        if not self.approvalobject:
            self.approvalobject = ApprovalObject.setup(
                name="Project's default approval object",
                approvalobjecttype=self.project.approval_object_type)
            self.save()

    def update_approved_status(self, approvalobject):
        if approvalobject.approved:
            self.approved = True
        elif approvalobject.disapproved:
            self.approved = False
        else:
            self.approved = None
        self.save()


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
    initialcrest = models.FloatField(null=True, blank=True)
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
        return self.shortname_dutch or self.name


class Result(models.Model):
    """result properties:
    better name is RawResult

    - belongs to a single scenario

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

    @property
    def absolute_resultloc(self):
        """Return absolute location, as a byte string, with path
        separators for this OS."""
        dest_dir = Setting.objects.get(key='destination_dir').value
        abspath = os.path.join(dest_dir, self.resultloc)
        if os.path.sep == '/':
            abspath = abspath.replace('\\', '/')
        else:
            abspath = abspath.replace('/', '\\')
        return abspath.encode('utf8')

    def __unicode__(self):
        return (
            '{t} for scenario {i} ({n})'
            .format(t=self.resulttype, i=self.scenario_id, n=self.scenario))


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

    shared_by = models.ForeignKey(User, null=True)

    class Meta:
        unique_together = ('scenario', 'new_project')
