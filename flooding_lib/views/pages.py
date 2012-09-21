"""Views for standalone pages."""

import logging

from flooding_lib import models
from flooding_lib.views import classbased

logger = logging.getLogger(__name__)


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

        return scenarios
