from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
import os.path

from flooding_lib.models import Region, Scenario
from flooding_base.models import Setting as BaseSetting

import logging

logger = logging.getLogger(__name__)


class ExportRun(models.Model):
    """
    An export run of one or more scenarios to generate a
    GIS map of the maximal water depth map.
    """
    class Meta:
        verbose_name = _('Export run')
        verbose_name_plural = _('Export runs')
        permissions = (
            ("can_create", "Can create export"),
            ("can_download", "Can download exportresult"),
        )
        ordering = ["creation_date"]

    EXPORT_TYPE_WATER_DEPTH_MAP = 10

    EXPORT_TYPE_CHOICES = (
        (EXPORT_TYPE_WATER_DEPTH_MAP, _('Water depth map')),
        )

    EXPORT_STATE_WAITING = 10
    EXPORT_STATE_ACTION_REQUIRED = 20
    EXPORT_STATE_APPROVED = 30
    EXPORT_STATE_DISAPPROVED = 40
    EXPORT_STATE_DONE = 50

    EXPORT_STATE_CHOICES = (
        (EXPORT_STATE_WAITING, _('Waiting')),
        (EXPORT_STATE_DONE, _('Klaar')))

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    export_type = models.IntegerField(
        choices=EXPORT_TYPE_CHOICES,
        default=EXPORT_TYPE_WATER_DEPTH_MAP)  # Obsolete: replaced
                                              # with export_* below

    export_max_waterdepth = models.BooleanField(
        default=True, verbose_name=_('The maximal waterdepth'))
    export_max_flowvelocity = models.BooleanField(
        default=True, verbose_name=_('The maximal flowvelocity'))
    export_possibly_flooded = models.BooleanField(
        default=True, verbose_name=_('The flooded area'))
    export_arrival_times = models.BooleanField(
        default=True, verbose_name=_('The arrival times'))
    export_period_of_increasing_waterlevel = models.BooleanField(
        default=True, verbose_name=_('The period of increasing waterlevel'))
    export_inundation_sources = models.BooleanField(
        default=True, verbose_name=_('The sources of inundation'))

    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    creation_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Creation date'))
    run_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Run date'))
    approved_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Approved date'))
    scenarios = models.ManyToManyField(Scenario)
    gridsize = models.PositiveIntegerField(
        default=50, verbose_name=_('Gridsize'))
    state = models.IntegerField(
        choices=EXPORT_STATE_CHOICES,
        default=EXPORT_STATE_WAITING)

    @property
    def selected_maps(self):
        """Return list with verbose_names of selected maps."""
        maps = []

        for fieldname in (
            'export_max_waterdepth',
            'export_max_flowvelocity',
            'export_possibly_flooded',
            'export_arrival_times',
            'export_period_of_increasing_waterlevel',
            'export_inundation_sources'
        ):
            if getattr(self, fieldname):
                maps.append(
                    ExportRun._meta.get_field_by_name(fieldname)[0]
                    .verbose_name.capitalize())
        return maps

    @property
    def meta_scenarios(self):
        """Return a list with id, name, projectname of
        selected scenarios."""
        scenarios_meta = []
        for scenario in self.scenarios.all():
            scenarios_meta.append({
                'id': scenario.id,
                'name': scenario.name,
                'project': scenario.main_project.name})
        return scenarios_meta

    def get_main_result(self):
        # Why RESULT_AREA_COUNTRY only?
        # results = self.result_set.filter(area=Result.RESULT_AREA_COUNTRY)
        results = self.result_set.all()
        # print self.id, results
        if results:
            return results[0]
        else:
            return None

    def all_active_scenarios(self):
        """Return all not archived scenarios attached to this export."""
        return self.scenarios.filter(archived=False)

    def __unicode__(self):
        return self.name

    def input_files(self, export_result_type):
        """
        Return a list of dictionaries, containing:
            'scenario': a scenario object,
            'dijkringnr': a region's dijkring number,
            'filename': the file containing this result type

        For each of this object's scenarios, for each of the regions
        of those scenarios, for the given result type (name or
        resulttype instance).
        """
        dest_dir = BaseSetting.objects.get(key='destination_dir').value

        if isinstance(export_result_type, basestring):
            # Name of result type given
            resulttype_filter = {'resulttype__name': export_result_type}
        else:
            # Result type itself
            resulttype_filter = {'resulttype': export_result_type}

        result = []
        for s in self.scenarios.all():
            for r in Region.objects.filter(breach__scenario=s):
                for rs in s.result_set.filter(**resulttype_filter):
                    result.append({
                        'scenario': s,
                        'dijkringnr': r.dijkringnr,
                        'filename': os.path.join(dest_dir, rs.resultloc)
                    })

        return result

    def create_general_file_for_gis_operation(self, file_location):
        """" Create a file with general information

        The information consists of the gridsize and the name of the
        export run.  The file is saved on the file_location

        """

        text_file = open(file_location, "w")
        text_file.write("Export run name: " + self.name + "\n")
        text_file.write("ExportId: " + str(self.id) + "\n")
        text_file.write("Gridsize: " + str(self.gridsize))

        text_file.close()


class Result(models.Model):
    """ A result from an export run.


    """

    class Meta:
        verbose_name = _('Result')
        verbose_name_plural = _('Results')

    RESULT_AREA_DIKED_AREA = 10
    RESULT_AREA_PROVINCE = 20
    RESULT_AREA_COUNTRY = 30

    RESULT_AREA_CHOICES = (
        (RESULT_AREA_DIKED_AREA, _('Diked area')),
        (RESULT_AREA_PROVINCE, _('Province')),
        (RESULT_AREA_COUNTRY, _('Country')),
        )

    name = models.CharField(max_length=200)
    file_basename = models.CharField(max_length=100)
    area = models.IntegerField(choices=RESULT_AREA_CHOICES)
    export_run = models.ForeignKey(ExportRun)

    def __unicode__(self):
        return self.name


class Setting(models.Model):
    """Stores settings for the export tool"""
    key = models.CharField(max_length=200, unique=True)
    value = models.CharField(max_length=200)
    remarks = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u'%s = %s' % (self.key, self.value)
