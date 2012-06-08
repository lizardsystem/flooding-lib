from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils.translation import ugettext as _
import os.path

from lizard_flooding.models import Region, Scenario
from flooding_base.models import Setting as BaseSetting

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
         #(EXPORT_STATE_ACTION_REQUIRED, _('Action required')),
         #(EXPORT_STATE_APPROVED, _('Approved')),
         #(EXPORT_STATE_DISAPPROVED, _('Disapproved')),
         (EXPORT_STATE_DONE, _('Klaar')),
        )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    export_type = models.IntegerField(choices=EXPORT_TYPE_CHOICES, default=EXPORT_TYPE_WATER_DEPTH_MAP)
    owner = models.ForeignKey(User)
    creation_date = models.DateTimeField(blank=True, null=True)
    run_date = models.DateTimeField(blank=True, null=True)
    approved_date = models.DateTimeField(blank=True, null=True)
    scenarios = models.ManyToManyField(Scenario)
    gridsize = models.PositiveIntegerField(default=50)
    state = models.IntegerField(choices=EXPORT_STATE_CHOICES, default=EXPORT_STATE_WAITING)

    def get_main_result(self):
        results = self.result_set.filter(area=Result.RESULT_AREA_COUNTRY)
        if results:
            return results[0]
        else:
            return None

    def __unicode__(self):
        return self.name

    def create_csv_file_for_gis_operation(self, export_result_type, csv_file_location):
        """
        Returns a csv file containing the:
        * the region ids
        * the result files (e.g. ASCII) related to the scenario(s) for the region with that region id

        Inputparameter:
        * export_result_type (integer): the type of the result of the scenario (e.g. max. water depth (=1))
        * csv_file_location: the file_location to store the csv file

        The information is gathered by:
        1) looping over the scenarios,
        2) the regions of that scenario,
        3) the results with the specifief result_type of that scenario
        """
        dest_dir = BaseSetting.objects.get(key = 'destination_dir').value

        information =[]
        for s in self.scenarios.all():
            for r in Region.objects.filter(breach__scenario__id=s.id).all():
                for rs in s.result_set.filter(resulttype=export_result_type):
                    information += [(r.dijkringnr, os.path.join(dest_dir, rs.resultloc))]

        import csv
        writer = csv.writer(open(csv_file_location, "wb"))
        writer.writerow(['dijkring', 'bestandslocatie'])
        writer.writerows(information)

    def create_general_file_for_gis_operation(self, file_location):
        """" Create a file with general information

        The information consists of the gridsize and the name of the export run.
        The file is saved on the file_location

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
    file_location = models.CharField(max_length=100)
    area = models.IntegerField(choices=RESULT_AREA_CHOICES)
    export_run = models.ForeignKey(ExportRun)


class Setting(models.Model):
    """Stores settings for the export tool"""
    key = models.CharField(max_length=200, unique = True)
    value = models.CharField(max_length=200)
    remarks = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u'%s = %s'%(self.key, self.value)
