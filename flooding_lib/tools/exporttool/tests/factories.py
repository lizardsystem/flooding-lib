import factory

from flooding_lib.tests.test_models import UserF
from flooding_lib.tools.exporttool import models


class ExportRunF(factory.DjangoModelFactory):
    class Meta:
        model = models.ExportRun

    owner = factory.SubFactory(UserF)
