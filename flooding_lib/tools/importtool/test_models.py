import factory
import mock

from django.test import TestCase
from django.contrib.auth.models import User

from flooding_lib.tools.importtool import models

class UserF(factory.Factory):
    FACTORY_FOR = User

    username = 'remco'

remco = UserF()
remco.save()

class ImportScenarioF(factory.Factory):
    FACTORY_FOR = models.ImportScenario

    name = 'test'
    owner = remco

class ImportScenarioInputFieldF(factory.Factory):
    FACTORY_FOR = models.ImportScenarioInputField

    importscenario = factory.LazyAttribute(lambda a: ImportScenarioF())
    validation_remarks = ''


class InputFieldF(factory.Factory):
    FACTORY_FOR = models.InputField

    name = 'test'
    header = models.InputField.HEADER_REMAINING
    position = 0


class TestImportScenarioInputField(TestCase):
    def get_resulting_isif(self, inputfield_type, inputfield_name, value_in):
        """Create a new scenario and an inputfield of type inputfield_type and
        name inputfield_name. Set its value in this scenario to value_in.
        Then get the input field back from the database, get the filled in
        ImportScenarioInputField back from the database, and return it."""

        import_scenario = ImportScenarioF()
        import_scenario.save()

        input_field = InputFieldF(
            type=inputfield_type, name=inputfield_name)
        input_field.save()

        isif = ImportScenarioInputFieldF(
            importscenario=import_scenario, inputfield=input_field)
        isif.setValue(value_in)

        input_field_from_db = (
            models.InputField.objects.get(name=inputfield_name))

        isif_from_db = models.ImportScenarioInputField.objects.get(
            importscenario=import_scenario,
            inputfield=input_field_from_db)

        return isif_from_db

    def testSetGetInteger(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_INTEGER, 'test_integer', 10)
        self.assertEquals(isif.getValue(), 10)

    def testSetGetFloat(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_FLOAT, 'test_float', 10.5)
        self.assertEquals(isif.getValue(), 10.5)

