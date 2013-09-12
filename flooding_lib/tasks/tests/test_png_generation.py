import mock
import numpy

from django.test import TestCase

from flooding_lib.tasks import png_generation
from flooding_lib.tools.importtool.test_models import InputFieldF


class TestCorrectGridta(TestCase):
    def trivial_test(self):
        inputfield = InputFieldF.create()

        mock_result = mock.MagicMock()
        mock_result.scenario.value_for_inputfield.return_value = 100.0 / 24

        grid = numpy.array([-999, 0, 50, 150])

        # -999 must be untouched
        # 0 and are too low, untouched
        # 100 should be subtracted from 150
        with mock.patch(
            'flooding_lib.tasks.'
            'png_generation.INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID',
            new=inputfield.id):
            png_generation.correct_gridta(grid, mock_result)

        self.assertTrue((grid == numpy.array([-999, 0, 50, 50])).all())
