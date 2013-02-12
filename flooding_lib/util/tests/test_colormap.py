import mock
import numpy

from unittest import TestCase

from flooding_lib.util import colormap


class TestToColorTuple(TestCase):
    def test_raises_value_error_if_too_long(self):
        self.assertRaises(
            ValueError,
            lambda: colormap.to_color_tuple("#ffffff"))
        self.assertRaises(
            ValueError,
            lambda: colormap.to_color_tuple("ffffff\n"))


class TestColorMap(TestCase):
    def _colormap_with_mock_file(self, lines):
        mock_open_file = mock.MagicMock()
        mock_open_file.__iter__.return_value = iter(lines)
        mock_open = mock.MagicMock(return_value=mock_open_file)

        with mock.patch('__builtin__.open', mock_open):
            return colormap.ColorMap("/")

    def setUp(self):
        lines = [
            "leftbound,color\n",
            "0.0,111111\n",
            "1.0,ffffff\n"
            ]

        self.cm = self._colormap_with_mock_file(lines)

    def test_no_exception_if_error_in_file(self):
        lines = [
            "whee\n",
            "0.0,1234567\n"
            ]
        self._colormap_with_mock_file(lines)

    def test_constructor(self):
        self.assertEquals(self.cm.leftbounds, [0.0, 1.0])
        self.assertEquals(self.cm.colors, [(17, 17, 17), (255, 255, 255)])

    def test_value_to_color_works(self):
        self.assertEquals(self.cm.value_to_color(0.5), (17, 17, 17))

    def test_value_to_color_leftbound_is_exclusive(self):
        self.assertEquals(self.cm.value_to_color(0.0), None)

    def test_value_to_color_below_is_none(self):
        self.assertEquals(self.cm.value_to_color(-1.0), None)

    def test_value_above_is_max_color(self):
        self.assertEquals(self.cm.value_to_color(2.0), (255, 255, 255))

    def test_2x2_grid_apply(self):
        grid = numpy.array([[0.5, -1],
                            [-1, -1]])

        colorgrid = self.cm.apply_to_grid(grid)

        # 0, 0 is opaque and color 17,17,17
        self.assertEquals(colorgrid[3, 0, 0], 255)
        self.assertEquals(colorgrid[0, 0, 0], 17)
        self.assertEquals(colorgrid[1, 0, 0], 17)
        self.assertEquals(colorgrid[1, 0, 0], 17)

        # Other points are transparent
        self.assertEquals(colorgrid[3, 0, 1], 0)
        self.assertEquals(colorgrid[3, 1, 0], 0)
        self.assertEquals(colorgrid[3, 1, 1], 0)
