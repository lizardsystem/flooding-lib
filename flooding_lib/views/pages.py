"""Views for standalone pages."""

import logging

import json

from django.core.urlresolvers import reverse

from flooding_presentation.views import external_file_location

from flooding_lib import models
from flooding_lib.views import classbased
from flooding_lib.util import geo

logger = logging.getLogger(__name__)

PRESENTATIONTYPE_MAX_WATERDEPTH = 11

class BreachInfoView(classbased.BaseView):
    required_permission = models.UserPermission.PERMISSION_SCENARIO_VIEW
    template_name = 'flooding/breachinfo.html'

    @property
    def project(self):
        return models.Project.objects.get(pk=self.project_id)

    @property
    def breach(self):
        return models.Breach.objects.get(pk=self.breach_id)

    def scenarios(self):
        """Return a queryset of all scenarios in this project that are
        connected to this breach."""
        scenarios = list(self.permission_manager.get_scenarios(
            breach=self.breach,
            permission=self.required_permission).filter(
            scenarioproject__project=self.project).order_by('id'))

        for scenario in scenarios:
            scenario.frequency = max(
                scenariobreach.extwrepeattime
                for scenariobreach in scenario.scenariobreach_set.all())
            scenario.inundated_area = scenario.get_result(
                shortname_dutch="overstroomd gebied")
            scenario.inundation_volume = scenario.get_result(
                shortname_dutch="inundatievolume")
            try:
                scenario.max_waterdepth_image = self._max_water_depth_image(
                    scenario)
                scenario.max_waterdepth_extent = self._get_water_depth_extent(
                    scenario)
            except Exception as e:
                logger.debug(e)

        return scenarios

    def _max_water_depth_image(self, scenario):
        pl = scenario.presentationlayer.filter(
            presentationtype__id=PRESENTATIONTYPE_MAX_WATERDEPTH)[0]
        url = reverse('presentation')
        return '{url}?action=get_gridframe&result_id={id}'.format(
            url=url, id=pl.id)

    def _get_water_depth_extent(self, scenario):
        pl = scenario.presentationlayer.filter(
            presentationtype__id=PRESENTATIONTYPE_MAX_WATERDEPTH)[0]
        pgn = pl.presentationgrid.png_default_legend.file_location
        pgn = external_file_location(pgn)

        return json.dumps(geo.GeoImage(pgn).extent())
