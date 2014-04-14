"""Views for standalone pages."""

import excel_response
import json
import logging
import os

from django.core.urlresolvers import reverse

from flooding_presentation.views import external_file_location

from flooding_base import models as basemodels
from flooding_lib import models
from flooding_lib.conf import settings
from flooding_lib.permission_manager import receives_permission_manager
from flooding_lib.templatetags.human import readable
from flooding_lib.tools.pyramids import pyramids
from flooding_lib.util import geo
from flooding_lib.views import classbased

logger = logging.getLogger(__name__)

PRESENTATIONTYPE_MAX_WATERDEPTH = 41
INUNDATION_PER_HOUR_RESULT_TYPE = 32


class BreachInfoView(classbased.BaseView):
    required_permission = models.UserPermission.PERMISSION_SCENARIO_VIEW
    template_name = 'flooding/breachinfo.html'
    raster_server_url = settings.RASTER_SERVER_URL

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
                scenario.max_waterdepth_layer = self._max_water_depth_layer(
                    scenario)
                scenario.max_waterdepth_extent = self._get_water_depth_extent(
                    scenario)
                scenario.inundation_statistics_url = (
                    self._get_inundation_statistics_url(scenario))
            except Exception as e:
                logger.debug(e)

        return scenarios

    def _max_water_depth_layer(self, scenario):
        pl = scenario.presentationlayer.filter(
            presentationtype__id=PRESENTATIONTYPE_MAX_WATERDEPTH)[0]
        result = pyramids.get_result_by_presentationlayer(pl)
        if result is not None and result.raster:
            return result.raster.layer

    def _get_water_depth_extent(self, scenario):
        pl = scenario.presentationlayer.filter(
            presentationtype__id=PRESENTATIONTYPE_MAX_WATERDEPTH)[0]
        result = pyramids.get_result_by_presentationlayer(pl)
        png = external_file_location(result.absolute_resultloc)
        logger.debug("PGN location:\n{}".format(png))
        extent = json.dumps(geo.GeoImage(png).extent())
        logger.debug(extent)
        return extent

    def _get_inundation_statistics_url(self, scenario):
        # 1. Find out whether this scenario has a statistics JSON
        #    file.  if not, return None.
        try:
            scenario.result_set.get(
                resulttype__id=INUNDATION_PER_HOUR_RESULT_TYPE)
        except models.Result.DoesNotExist:
            return None

        # 2. Otherwise, return an URL to a page that shows the data.
        return reverse(
            'flooding_inundationstats_page',
            kwargs={'scenario_id': scenario.id})


@receives_permission_manager
def breachinfo_excel(request, permission_manager, project_id, breach_id):
    # Reuse the class-based view...
    view = BreachInfoView()
    view.project_id = project_id
    view.breach_id = breach_id
    view.permission_manager = permission_manager

    data = [
        ["ID", "Scenario", "Orig. project", "Overschrijdingsfreq",
         "Schade o.g.", "Slachtoffers", "Oppervlak o.g."],
        ]

    data += [
        [scenario.id,
         unicode(scenario).encode('utf8'),
         unicode(scenario.main_project).encode('utf8'),
         scenario.frequency,
         readable(scenario.financial_damage() or ""),
         scenario.casualties(),
         readable(scenario.inundated_area.value or "")
         ]
        for scenario in view.scenarios()]

    return excel_response.ExcelResponse(
        data,
        'bresinfo_project_{0}_bres_{1}'.format(project_id, breach_id))


class InundationStatsView(classbased.BaseView):
    template_name = 'flooding/inundationstats.html'

    @property
    def scenario(self):
        return models.Scenario.objects.get(pk=self.scenario_id)

    def inundation_stats(self):
        try:
            result = self.scenario.result_set.get(
                resulttype__id=INUNDATION_PER_HOUR_RESULT_TYPE)
        except models.Result.DoesNotExist:
            return []

        jsonfile = os.path.join(
            basemodels.Setting.objects.get(
                key='DESTINATION_DIR').value.replace('\\', '/'),
            result.resultloc)

        if not os.path.exists(jsonfile):
            return []

        jsonstring = file(jsonfile).read()
        stats = json.loads(jsonstring)

        # Make the timestamps ints
        for hour in stats:
            hour['timestamp'] = int(hour['timestamp'])

        return stats
