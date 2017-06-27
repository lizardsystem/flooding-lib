"""models factories"""
from datetime import datetime
import factory


from flooding_lib.tests.test_models import UserF
from flooding_lib.tools.gdmapstool.models import GDMapProject
from flooding_lib.tools.gdmapstool.models import GDMap


class GDMapProjectF(factory.DjangoModelFactory):
    class Meta:
        model = GDMapProject

    name = "Test 1"
    description = "Test gebiedsdekkend kaarten project"
    owner = factory.SubFactory(UserF)
    creation_date = datetime.now()


class GDMapF(factory.DjangoModelFactory):
    class Meta:
        model = GDMap

    name = "Test gebeidsdekkende map"
    creation_date = datetime.now()
    gd_map_project = factory.SubFactory(GDMapProjectF)

    @factory.post_generation
    def scenarios(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for scenario in extracted:
                self.scenarios.add(scenario)
