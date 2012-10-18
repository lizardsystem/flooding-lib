"""Views to do with zip files."""

import logging
import os
import tempfile
import zipfile

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse

from flooding_lib import models
from flooding_lib import permission_manager
from flooding_lib.util import files

logger = logging.getLogger(__name__)


class FixedFileWrapper(FileWrapper):
    """This is a hack for https://code.djangoproject.com/ticket/6027 .
    Use it only for returning zip files in temp files."""
    def __iter__(self):
        self.filelike.seek(0)
        return self


def result_location(p):
    return os.path.join(
        settings.EXTERNAL_RESULT_MOUNTED_DIR,
        p.replace('\\', '/'))


@permission_manager.receives_permission_manager
def scenario_results_zipfile(request, permission_manager, scenario_id):
    """Return all results of a given scenario as one large
    zipfile. Requires approval permissions in the scenario."""

    scenario = models.Scenario.objects.get(pk=scenario_id)

    if not permission_manager.check_scenario_permission(
        scenario, models.UserPermission.PERMISSION_SCENARIO_APPROVE):
        raise PermissionDenied()

    results = scenario.result_set.all()

    resultset = set()

    for result in results:
        resultloc = result.resultloc
        if not resultloc:
            continue

        resultloc = result_location(resultloc)

        if os.path.exists(resultloc):
            resultset.add(resultloc)

    # We use a mkstemp file, which will be automatically closed and
    # removed once there are no more references to it.
    temp = tempfile.TemporaryFile(
        prefix="zipfile_for_downloading_scenario_results",
        dir=settings.TMP_DIR)

    zipf = zipfile.ZipFile(temp, mode='w')

    for loc in resultset:
        filename = os.path.basename(loc)
        if filename.endswith('.zip'):
            with files.temporarily_unzipped(loc) as paths:
                for path in paths:
                    zipf.write(
                        path, os.path.basename(path), zipfile.ZIP_DEFLATED)
        else:
            zipf.write(loc, filename, zipfile.ZIP_DEFLATED)

    zipf.close()

    # By wrapping the temp file in a Django FileWrapper, it should be
    # read in in chunks that always fit into memory.
    wrapper = FixedFileWrapper(temp)

    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = (
        'attachment; filename=resultaten_scenario_{0}.zip'.format(scenario.id))
    # temp.tell() is the current position in the file, which is the
    # same as the length of the file
    response['Content-Length'] = temp.tell()

    # But for serving from this opened file, we have to start at the
    # beginning
    temp.seek(0)

    return response
