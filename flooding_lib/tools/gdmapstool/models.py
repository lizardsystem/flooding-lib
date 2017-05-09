from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from flooding_lib.models import Scenario


class GDMapProject(models.Model):
    """
    Project for gebiedsdekkende maps.
    """

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    creation_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Creation date'))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Gebiedsdekkende map project')
        verbose_name_plural = _('Gebiedsdekkende map projects')
        ordering = ["creation_date"]


class GDMap(models.Model):
    """
    Gebiedsdekkende map.
    """
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    creation_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Creation date'))
    gd_map_project = models.ForeignKey(GDMapProject, verbose_name=_('GD map project'))
    scenarios = models.ManyToManyField(Scenario, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def meta_scenarios(self):
        """Return a list with id, name, projectname of
        selected scenarios."""
        scenarios_meta = []
        for scenario in self.scenarios.all():
            scenarios_meta.append({
                'id': scenario.id,
                'name': scenario.name})
        return scenarios_meta

    class Meta:
        verbose_name = _('Gebiedsdekkende map')
        verbose_name_plural = _('Gebiedsdekkende maps')
        ordering = ["name"]
