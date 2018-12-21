# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division


from flooding_lib.views import infowindow
from flooding_lib.services import service
from flooding_lib.tests import test_models
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tests import utils

from nose.plugins.attrib import attr


@attr('fields')
class TestInfoWindow(utils.UserTestCase):

    def setUp(self):
        super(TestInfoWindow, self).setUp()

        # have a general project with related models in the database
        self.project = test_models.ProjectF.create()
        self.risk_fields = {'fl_rk_adm_jud': 2, 'fl_rk_dpv_ref_part': 3}
        breach = test_models.BreachF.create(
            administrator=1, **self.risk_fields
        )
        sobekmodel = test_models.SobekModelF.create()
        test_models.BreachSobekModelF.create(
            sobekmodel=sobekmodel,
            breach=breach,
        )
        self.scenario = test_models.ScenarioF.create(
            sobekmodel_inundation=sobekmodel,
        )
        self.scenario.set_project(self.project)
        test_models.ScenarioBreachF.create(
            scenario=self.scenario, breach=breach
        )
        self.scenario.save()
        self.project.save()

        # create an inputfield for the breach administrator
        self.administrator_name = 'GraafLangeDijk'
        test_models.InputFieldF.create(
            name='Beheerder',
            header=InputField.HEADER_BREACH,
            destination_table='Breach',
            destination_field='administrator',
            options='{1: "%s"}' % self.administrator_name,
        )

    def test_infowindow_contains_administrator(self):
        url = '/infowindow/?scenarioid=%s&action=information'
        request = self.superuser_request(url % self.scenario.pk)
        response = infowindow.infowindow(request)
        self.assertTrue(self.administrator_name in response.content)

    def test_scenarios_export_list_contains_risks(self):
        url = '/service/?action=get_scenarios_export_list&project_id=%s'
        request = self.superuser_request(url % self.project.pk)
        response = service(request)
        self.assertTrue(all(k in response.content
                            for k in self.risk_fields.keys()))
