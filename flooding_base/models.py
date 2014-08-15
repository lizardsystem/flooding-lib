# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.utils.safestring import SafeString

from flooding_base.eidatabaseconnector import ConnectDatabase2EiServer
from flooding_base.dummydatabaseconnector import DummyDatabaseConnector


class Configuration(models.Model):
    """Stores the datasource type and some meta data"""

    DATASOURCE_TYPE_CHOICES = (
        (1, _('DataSourceEI')),
        (2, _('DataSourceDummy')),
        )
    DATASOURCE_TYPE_EI = 1
    DATASOURCE_TYPE_DUMMY = 2

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # datasource_type tells us to link in the DataSourceEI table or a
    # different table
    datasourcetype = models.IntegerField(choices=DATASOURCE_TYPE_CHOICES)

    groups = models.ManyToManyField(Group,
                                    through='GroupConfigurationPermission')

    #geographic coordinates
    coords_w = models.FloatField(default=3.289)
    coords_e = models.FloatField(default=7.314)
    coords_s = models.FloatField(default=50.765)
    coords_n = models.FloatField(default=53.471)

    class Meta:
        verbose_name = _('Configuration')
        verbose_name_plural = _('Configurations')
        db_table = 'base_configuration'

    def __unicode__(self):
        return self.name

    def getConnector(self):
        """Return connector, according to datasourcetype"""
        if self.datasourcetype == self.DATASOURCE_TYPE_EI:
            return self.datasourceei.getConnector()
        elif self.datasourcetype == self.DATASOURCE_TYPE_DUMMY:
            return self.datasourcedummy.getConnector()
        return None

    def get_datasource(self):
        """Return datasource object"""
        if self.datasourcetype == self.DATASOURCE_TYPE_EI:
            return self.datasourceei
        elif self.datasourcetype == self.DATASOURCE_TYPE_DUMMY:
            return self.datasourcedummy
        return None

    def hasDataSource(self):
        try:
            self.getConnector()
            return True
        except:
            return False

    def getSpecificData(self):
        """Get datasource specific data in a dictionary"""
        if self.datasourcetype == self.DATASOURCE_TYPE_EI:
            return self.datasourceei.getSpecificData()
        elif self.datasourcetype == self.DATASOURCE_TYPE_DUMMY:
            return self.datasourcedummy.getSpecificData()
        return None


class DataSourceEI(models.Model):
    """datasource types for EI connection (i.e. Jdbc2Ei)"""

    configuration = models.OneToOneField(Configuration, unique=True)
    # configuration must be unique
    connectorurl = models.CharField(
        max_length=200,
        default='http://127.0.0.1:8080/Jdbc2Ei/test')
    databaseurl = models.CharField(
        max_length=200,
        default='jdbc:vjdbc:rmi://127.0.0.1:2000/VJdbc,FewsDataStore')
    databaseurltagname = models.CharField(max_length=200)

    usecustomfilterresponse = models.BooleanField(default=False)
    customfilterresponse = models.TextField(
        null=True, blank=True,
        help_text=("Use a pythonic list of dictionaries. The rootnode has "
                   "'parentid': None. i.e. [{'id':'id','name':'name',"
                   "'parentid':None}, {'id':'id2','name':'name2',"
                   "'parentid':'id'}]"))

    class Meta:
        verbose_name = _('DataSourceEI')
        verbose_name_plural = _('Data sources EI')
        db_table = 'base_datasourceei'

    def __unicode__(self):
        return self.configuration.__unicode__()

    def getConnector(self):
        return ConnectDatabase2EiServer(self.connectorurl,
                                        self.databaseurl,
                                        self.databaseurltagname)

    def getSpecificData(self):
        connector = self.getConnector()
        try:
            databaseurl_actual = connector.getUrl()
        except:
            databaseurl_actual = 'Could not retrieve actual databaseurl'
        return {'databaseurl': self.databaseurl,
                'databaseurltagname': self.databaseurltagname,
                'databaseurl_actual': databaseurl_actual}


class DataSourceDummy(models.Model):
    """datasource type dummy connection"""

    configuration = models.OneToOneField(Configuration, unique=True)
    # configuration must be unique

    class Meta:
        verbose_name = _('DataSourceDummy')
        verbose_name_plural = _('Data sources dummy')
        db_table = 'base_datasourcedummy'

    def __unicode__(self):
        return self.configuration.__unicode__()

    def getConnector(self):
        return DummyDatabaseConnector()

    def getSpecificData(self):
        return {}


class Application(models.Model):
    """Lists all available applications"""
    TYPE_FEWS = 1
    TYPE_FLOODING = 2
    TYPE_FLOW = 3
    TYPE_PRESENTATION = 4
    TYPE_GISVIEWER = 5
    TYPE_MIS = 6
    TYPE_NHI = 7

    TYPE_CHOICES = (
        (TYPE_FEWS, 'fews'),
        (TYPE_FLOODING, 'flooding'),
        (TYPE_FLOW, 'flow'),
        (TYPE_PRESENTATION, 'presentation'),
        (TYPE_GISVIEWER, 'gisviewer'),
        (TYPE_MIS, 'mis'),
        (TYPE_NHI, 'nhi'),
        )
    TYPE_DICT = dict(TYPE_CHOICES)

    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'base_application'

    def __unicode__(self):
        return u'%s' % self.name

    def get_application_name(self):
        return self.TYPE_DICT[self.type]

    def get_subapplication_jsnames_str(self):
        """return jsnames in a string, seperated by comma.

        i.e. "fews_map, fews_graphs"

        """
        return ', '.join([sa.get_subapplication_jsname() for sa in
                          self.subapplication_set.all()])

    @classmethod
    def get_applications(cls, site=None):
        """Get all available applications. Optionally gives the
        applications for a given site.

        Returns a dictionary of key: js app name, value: application
        object, where active=True
        """
        if site is None:
            objects = cls.objects.filter(active=True)
        else:
            objects = Application.objects.filter(
                subapplication__in=site.subapplications.all(),
                active=True).distinct()
        return dict([(a.get_application_name(), a) for a in objects])


class SubApplication(models.Model):
    """
    Subapplications of application. Used by Site as starter application.

    DO NOT CHANGE TYPE_CHOICES WITHOUT KNOWING THE CONSEQUENCES
    """

    TYPE_CHOICES = (
        (11, 'fewsMap'),
        (12, 'fewsGraph'),
        (13, 'fewsReport'),
        (14, 'fewsConfig'),
        (21, 'floodingResults'),
        (22, 'floodingNew'),
        (23, 'floodingTable'),
        (24, 'floodingImport'),
        (25, 'floodingExport'),
        (31, 'flowResults'),
        (41, 'gisviewerMap'),
        (51, 'mis_map'),
        (52, 'mis_table'),
        (53, 'mis_report'),
        (54, 'mis_admin'),
        (55, 'mis_import'),
        (61, 'nhi_map'),
        )
    TYPE_DICT = dict(TYPE_CHOICES)
    NAME2TYPE = dict([(b, a) for (a, b) in TYPE_CHOICES])
    JSNAMES = {
        11: 'fews_map',
        12: 'fews_graphs',
        13: 'fews_report',
        14: 'fews_lcm',
        21: 'flooding_result',
        22: 'flooding_new',
        23: 'flooding_table',
        24: 'flooding_import',
        25: 'flooding_export',
        31: 'flow_result',
        41: 'gisviewer_map',
        51: 'mis_map',
        52: 'mis_table',
        53: 'mis_report',
        54: 'mis_admin',
        55: 'mis_import',
        61: 'nhi_map',
        }

    application = models.ForeignKey(Application)
    index = models.IntegerField(default=1)
    type = models.IntegerField(choices=TYPE_CHOICES)

    class Meta:
        ordering = ('application', 'index')
        db_table = 'base_subapplication'

    def __unicode__(self):
        return u'%s' % self.TYPE_DICT[self.type]

    def get_subapplication_name(self):
        return self.TYPE_DICT[self.type]

    def get_subapplication_jsname(self):
        return self.JSNAMES[self.type]


class GroupConfigurationPermission(models.Model):
    """Permission of groups on configurations"""
    PERMISSION_CHOICES = (
        (1, _('VIEW')),
        )

    PERMISSION_VIEW = 1

    configuration = models.ForeignKey(Configuration)
    group = models.ForeignKey(Group)
    permission = models.IntegerField(choices=PERMISSION_CHOICES, default=1)

    class Meta:
        db_table = 'base_groupconfigurationpermission'

    def __unicode__(self):
        return u'%s %s %s' % (self.group, self.configuration, self.permission)


class Setting(models.Model):
    """Stores settings for the project"""
    key = models.CharField(max_length=200, unique=True)
    value = models.CharField(max_length=200)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'base_setting'

    def __unicode__(self):
        return u'%s = %s' % (self.key, self.value)


class Map(models.Model):
    """Stores wms entries"""
    name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    url = models.CharField(max_length=200)

    #layernames separated with comma
    layers = models.TextField()

    transparent = models.NullBooleanField(default=None)
    is_base_layer = models.NullBooleanField(default=False)
    tiled = models.NullBooleanField(default=None)
    srs = models.CharField(max_length=50, default='EPSG:900913')

    class Meta:
        db_table = 'base_map'

    def __unicode__(self):
        return self.name

#possible extension: PermissionGroupSubApplication


class Site(models.Model):
    """Pre-configured sites"""
    name = models.CharField(max_length=200)
    configurations = models.ManyToManyField(Configuration,
                                            blank=True,
                                            null=True)

    maps = models.ManyToManyField(Map, null=True, blank=True)
    subapplications = models.ManyToManyField(SubApplication)
    #starter_app: subapp, because the app is then automatically defined too
    starter_application = models.ForeignKey(
        SubApplication,
        related_name='starter_application')

    favicon_image = models.ImageField(
        upload_to='user/favicon', null=True, blank=True)
    logo_image = models.ImageField(
        upload_to='user/logo', null=True, blank=True,
        help_text=_('The size is 280x45 pixels'))
    topbar_image = models.ImageField(
        upload_to='user/topbar', null=True, blank=True,
        help_text=_('The size is 600x70 pixels (width can vary)'))

    coords_w = models.FloatField(default=3.289)
    coords_e = models.FloatField(default=7.314)
    coords_s = models.FloatField(default=50.765)
    coords_n = models.FloatField(default=53.471)

    class Meta:
        db_table = 'base_site'

    def __unicode__(self):
        return self.name

    def get_applications(self):
        return Application.get_applications(site=self)

    def get_subapplication_jsnames_str(self):
        """return dict with per application the list of
        subapplications in a single string"""
        result = {}
        for app_name, a in self.get_applications().items():
            result[app_name] = ', '.join(
                [sa.get_subapplication_jsname()
                 for sa in self.subapplications.filter(application=a)])
        return result


class Text(models.Model):
    """Some text to show on the site, somewhere."""

    LANGUAGE_CHOICES = (('nl', 'Nederlands'),)
    slug = models.CharField(max_length=200)
    language = models.CharField(
        max_length=5, default="nl",
        choices=LANGUAGE_CHOICES)
    content = models.TextField(blank=True)
    is_html = models.BooleanField(default=False)

    @classmethod
    def get(cls, slug, language_code=None, request=None):
        """Returns the text's content, HTML-escaped unless it is
        itself HTML, and marked as a SafeString so that it can be used
        in templates immediately.

        If language_code is not given, it can be retrieved from the
        request, if that is given.

        If the text isn't found, a short text saying which slug should be
        entered into the admin interface is returned."""

        if language_code is None and request:
            language_code = getattr(request, 'LANGUAGE_CODE', None)

        search = {
            'slug': slug,
        }
        if language_code is not None:
            search['language'] = language_code

        texts = cls.objects.filter(**search)
        if texts.count() > 0:
            text = texts[0]
            if text.is_html:
                return SafeString(text.content)
            else:
                return SafeString(escape(text.content))
        else:
            return SafeString(escape(
        "Text not found. Enter a Text with slug '{0}' and language_code '{1}'."
                .format(slug, language_code if language_code else '')))

    def __unicode__(self):
        return "{slug} ({language})".format(
            slug=self.slug, language=self.language)
