from django.test import TestCase

from flooding_lib.tests import test_models
from flooding_lib.tasks import spawn

import mock

class TestFindResulttype(TestCase):

    def test_find_resulttype(self):
        filename = "test.asc"
        resulttypes = [
            test_models.ResultTypeF.build(
                name='test', content_names_re='test.asc')]
        self.assertEquals(
            'test',
            spawn.find_resulttype(filename, resulttypes).name)

class TestSaveOutputFiles(TestCase):

    def setUp(self):
        self.resulttypes = [
            test_models.ResultTypeF.build(
                id=1,
                name='gridflowvelocity_t',
                content_names_re='dm1c[0-9]*.asc'),
            test_models.ResultTypeF.build(
                id=2,
                name='gridwaterdepth_t',
                content_names_re='dm1d[0-9]*.asc')]
        self.output_dir_name = "/tmp"
        self.work_dir = "/tmp"

    def test_save_output_files_to_dest(self):
        comment_line = "/* run: dm1  , created\n"
        content = "ncols              632"
        filenames = ["dm1d0018.asc",
                     "dm1d0020.asc",
                     "dm1c0018.asc",
                     "dm1h0020.asc"]
        files = {}

        zipfile1 = mock.MagicMock()
        zipfile2 = mock.MagicMock()
        zipfiles = [zipfile1, zipfile2]
        def side_effect(*args, **kwargs):
            return zipfiles.pop(0)

        with mock.patch('os.listdir', return_value=filenames) as patched_listdir:
            with mock.patch('flooding_lib.tasks.spawn.ZipFile',
                            side_effect=side_effect):
                max_file_nr, min_file_nr = spawn.save_output_files_to_dest(
                    '/outputdir/', '/workdir/', self.resulttypes)                
                self.assertEquals(max_file_nr[1], 18)
                self.assertEquals(min_file_nr[1], 18)

                patched_listdir.assert_called_with('/workdir/')

                self.assertTrue(zipfile1.close.called)
                self.assertTrue(zipfile2.close.called)
