import factory
import mock

from django.test import TestCase
from django.contrib.auth.models import User

from flooding_lib.tools.importtool import models


class UserF(factory.Factory):
    FACTORY_FOR = User

    username = 'remco'


class ImportScenarioF(factory.Factory):
    FACTORY_FOR = models.ImportScenario

    name = 'test'
    owner = UserF.create()


class ImportScenarioInputFieldF(factory.Factory):
    FACTORY_FOR = models.ImportScenarioInputField

    importscenario = factory.LazyAttribute(lambda a: ImportScenarioF.build())
    validation_remarks = ''


class InputFieldF(factory.Factory):
    FACTORY_FOR = models.InputField

    name = 'test'
    header = models.InputField.HEADER_REMAINING
    type = models.InputField.TYPE_STRING
    position = 0


DAYFLOAT_FROM_INTERVALSTRING =\
    'flooding_lib.tools.importtool.models.get_dayfloat_from_intervalstring'


class TestImportScenarioInputField(TestCase):
    def get_resulting_isif(self, inputfield_type, inputfield_name, value_in):
        """Create a new scenario and an inputfield of type inputfield_type and
        name inputfield_name. Set its value in this scenario to value_in.
        Then get the input field back from the database, get the filled in
        ImportScenarioInputField back from the database, and return it."""

        import_scenario = ImportScenarioF.create()

        input_field = InputFieldF.create(
            type=inputfield_type, name=inputfield_name)

        isif = ImportScenarioInputFieldF.create(
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

    def testSetGetString(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_STRING, 'test_string', 'test_string')
        self.assertEquals(isif.getValue(), 'test_string')

    def testSetIntervalRaisesOnWrongFormat(self):
        self.assertRaises(ValueError, lambda: self.get_resulting_isif(
            models.InputField.TYPE_INTERVAL, 'test_interval', 0.0))

    def testSetGetInterval(self):
        with mock.patch(
            DAYFLOAT_FROM_INTERVALSTRING,
            new=mock.MagicMock(return_value=5.5)) as mocked_function:
            isif = self.get_resulting_isif(
                models.InputField.TYPE_INTERVAL, 'test_interval', '5 d 10:30')
            self.assertEquals(isif.getValue(), 5.5)
            mocked_function.assertCalledWith('5 d 10:30')


class TestImportScenario(TestCase):
    def testReceiveInputFields(self):
        testfields = {
            'test1': 'whee',
            'test2': 3
            }

        test1 = InputFieldF.create(
            name='test1',
            type=models.InputField.TYPE_STRING)
        test2 = InputFieldF.create(
            name='test2',
            type=models.InputField.TYPE_INTEGER)

        importscenario = ImportScenarioF.create()

        importscenario.receive_input_fields(testfields)

        try:
            isif = models.ImportScenarioInputField.objects.get(
                importscenario=importscenario, inputfield=test1)
        except models.ImportScenarioInputField.DoesNotExist:
            raise AssertionError(
                "importscenarioimportfield test1 does not exist")

        try:
            value = models.StringValue.objects.get(
                importscenario_inputfield=isif)
            self.assertEquals(value.value, 'whee')
        except models.StringValue.DoesNotExist:
            raise AssertionError("stringvalue does not exist")

        try:
            isif = models.ImportScenarioInputField.objects.get(
                importscenario=importscenario, inputfield=test2)
        except models.ImportScenarioInputField.DoesNotExist:
            raise AssertionError(
                "importscenarioimportfield test2 does not exist")

        try:
            value = models.IntegerValue.objects.get(
                importscenario_inputfield=isif)
            self.assertEquals(value.value, 3)
        except models.StringValue.DoesNotExist:
            raise AssertionError("integervalue does not exist")
