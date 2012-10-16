"""Views to do with zip files."""

import logging
import os
import StringIO
import zipfile

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from flooding_lib import models
from flooding_lib import permission_manager

logger = logging.getLogger(__name__)


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

    stringio = StringIO.StringIO()

    zipf = zipfile.ZipFile(stringio, mode='w')

    for loc in resultset:
        filename = os.path.basename(loc)
        if filename.endswith('.zip'):
            readzipf = zipfile.ZipFile(loc, mode='r')
            for name in readzipf.namelist():
                content = readzipf.read(name)
                zipf.writestr(name, content, zipfile.ZIP_DEFLATED)
        else:
            zipf.write(loc, filename, zipfile.ZIP_DEFLATED)

    zipf.close()

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = (
        'attachment; filename=resultaten_scenario_{0}.zip'.format(scenario.id))
    response.write(stringio.getvalue())
    stringio.close()
    return response
