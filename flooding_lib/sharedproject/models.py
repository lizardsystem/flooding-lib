##
# "Provincies" are responsible for delivering data to the ROR, but
# often the data comes from "waterschappen". Each waterschap has
# declared a province through which they will deliver their data.
#
# There is a required metadata field "Eigenaar overstromingsdata" in
# the shared scenarios that holds either a province or a waterschap,
# and we can use that to figure out which province a given scenario
# belongs to.

import json

from django.contrib.gis.db import models

import flooding_lib.models
#from flooding_lib.scenario_sharing import (
#    PROJECT_ROR, PROJECT_LANDELIJK_GEBRUIK)

# Eigenaar Overstromingsinformatie ExtraInfoField ID
OWNER_EXTRAINFOFIELD_ID = 7

import logging
logger = logging.getLogger(__name__)


class Province(models.Model):
    name = models.CharField(max_length=100)

    statistics = models.TextField(null=True) # Bit of JSON
                                             # representing the
                                             # dictionary with
                                             # computed scenario
                                             # statistics

    @classmethod
    def province_for(cls, scenario):
        if scenario.ror_province:
            return scenario.ror_province

        try:
            ownerid = flooding_lib.models.ExtraScenarioInfo.objects.get(
                extrainfofield__id=OWNER_EXTRAINFOFIELD_ID,
                scenario=scenario).value
        except flooding_lib.models.ExtraScenarioInfo.DoesNotExist:
            raise Province.DoesNotExist(
                "Verplichte metadata Eigenaar niet gevonden bij scenario {}".
                format(scenario))

        try:
            int(ownerid)
            return Owner.objects.get(id=ownerid).province
        except ValueError:
            return Owner.objects.get(name=ownerid).province

    def in_province(self, scenario):
        if not scenario.ror_province:
            scenario.ror_province = Province.province_for(scenario)
            scenario.save()
        return scenario.ror_province == self

    def scenario_stats(self, project, scenarios):
        if self.statistics:
            return json.loads(self.statistics)

        logger.debug('in scenario_stats')
        scenarios = [
            scenario for scenario in scenarios
            if self.in_province(scenario)]
        logger.debug('in scenario_stats 2')

        stats = {
            'amount': len(scenarios),
            'approved': len(list(
                s for s in scenarios if
                s.scenarioproject(project).approved)),
            'disapproved': len(list(
                s for s in scenarios if
                s.scenarioproject(project).approved == False))
            }
        logger.debug('in scenario_stats 3')

        stats['notyetapproved'] = (
            stats['amount'] - stats['approved'] - stats['disapproved'])

        logger.debug(stats)

        self.statistics = json.dumps(stats)
        self.save()

        return stats

    def __unicode__(self):
        return self.name


class Owner(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province)
