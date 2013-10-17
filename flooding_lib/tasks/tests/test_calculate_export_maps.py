from django.test import TestCase

import mock

from flooding_lib.tasks import calculate_export_maps


def cem(attr):
    """Helper function for patch, because the module name is so long."""
    return 'flooding_lib.tasks.calculate_export_maps.{attr}'.format(attr=attr)


class TestFixPath(TestCase):
    def test_turns_unicode_into_str(self):
        filename = u"filename"
        print(repr(calculate_export_maps.fix_path(filename)))
        self.assertTrue(
            isinstance(calculate_export_maps.fix_path(filename), str))


class TestAllFilesIn(TestCase):
    @mock.patch(cem('is_valid_zipfile'), return_value=False)
    @mock.patch('os.path.isfile', return_value=False)
    def test_non_existing_file_returns_nothing(self, patched1, patched2):
        self.assertEquals(
            list(calculate_export_maps.all_files_in('/some/file/name')),
            [])

    @mock.patch(cem('is_valid_zipfile'), return_value=False)
    @mock.patch('os.path.isfile', return_value=True)
    def test_existing_nonzip_file_returns_str(self, patched1, patched2):
        filename = u'filename'

        allfiles = list(calculate_export_maps.all_files_in(filename))

        self.assertEquals(len(allfiles), 1)
        self.assertEquals(allfiles[0], "filename")
        self.assertTrue(isinstance(allfiles[0], str))

    @mock.patch(cem('is_valid_zipfile'), return_value=True)
    def test_returns_files_in_zip(self, patched):
        files = ["file1", "file2"]

        mocked_unzipped = mock.MagicMock()
        mocked_unzipped.__enter__.return_value = mocked_unzipped
        mocked_unzipped.__iter__.return_value = iter(files)

        with mock.patch(
            'flooding_lib.util.files.temporarily_unzipped',
            return_value=mocked_unzipped):
            files2 = list(
                calculate_export_maps.all_files_in('/some/file/name'))

        self.assertEquals(files, files2)
