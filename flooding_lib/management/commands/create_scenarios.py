import csv
import os.path
from optparse import make_option
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from flooding_lib.models import Breach, Project
from flooding_lib.views.dev import service_save_new_scenario

log = logging.getLogger("")

class Request(object):
    POST = {}


class Command(BaseCommand):
    help = ("Example: bin/django create_scenarios scenario_csv cutoff_csv "
            "--log_level DEBUG")

    option_list = BaseCommand.option_list + (
            make_option('--log_level',
                        help='logging level 10=debug 50=critical',
                        default='DEBUG',
                        type='str'), )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No files given.")

        filename = args[0]
        if not os.path.exists(filename) or os.path.isdir(filename):
            raise CommandError("'{0}' is not an existing file.".
                               format(filename))

        numeric_level = getattr(logging, options["log_level"].upper(), None)
        if not isinstance(numeric_level, int):
            log.warning("Invalid log level: %s" % options["log_level"])
            numeric_level = 10

        log.setLevel(numeric_level)

        # open csv file
        csvfile = open(filename, 'rb')

        # check dialect. Dutch excel versions use ';' as delimiter
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,")
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)

        # open optional cuttoff location file
        try:
            filename_cuttoffs = args[1]
            if not os.path.exists(filename_cuttoffs) or os.path.isdir(filename_cuttoffs):
                raise CommandError("'{0}' is not an existing file.".
                                   format(filename_cuttoffs))
            reader_cutoffs = csv.DictReader(open(filename_cuttoffs, 'rb'),
                                            dialect=dialect)

            cutoffs = [c for c in reader_cutoffs]

        except IndexError:
            log.warning("No cuttoff location file provided. Continue without cuttoffs.")
            cutoffs = []

        except CommandError, e:
            log.error(e.message)
            raise CommandError(e)

        requests = []

        for line in reader:
            log.debug('regel: {0}'.format(line))

            username = line.get('username')
            projectname = line.get('projectname')
            breach_id = line.get('breach_id')
            scenario_time_h = line.get('scenario_time_h', 48)
            cutoff_set = line.get('cutoff_set', None)

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise User.DoesNotExist("Username '{0}' does not exist".format(username))

            try:
                project = Project.objects.filter(name=projectname)[0]
            except IndexError:
                raise Project.DoesNotExist("projectname '{0}' does not exist".format(projectname))

            tsim_ms = int(scenario_time_h) * 3600 * 1000

            try:
                breach = Breach.objects.get(pk=int(breach_id))
            except Breach.DoesNotExist:
                raise Breach.DoesNotExist("breach id '{0}' does not exist".format(breach_id))

            inundation_model = breach.region.sobekmodels\
                .filter(active=True).order_by('-id')[0]

            externalwater_model = breach.externalwater\
                .sobekmodels.filter(active=True).order_by('-id')[0]

            if inundation_model is None:
                raise ValueError("No active innundation model for breach {0}".format(breach))

            if externalwater_model is None:
                raise ValueError("No active externalwater model for breach {0}".format(breach))

            cutoff_str = []
            if cutoff_set is not None:

                set_cutoffs = [(cutoff['cutoff_id'], cutoff.get('close_time_h', 0)) for cutoff
                           in cutoffs if cutoff['cutoff_set'] == cutoff_set]

                for cutoff in set_cutoffs:

                    cutoff_str.append('{0}|1|{1}'.format(cutoff[0],
                                                         int(cutoff[1])*3600*1000))

            waterlevel = float(line.get('waterlevel', -0.4))

            request = Request()
            request.user = user
            request.POST = {
                # for scenario
                'tsim_ms': tsim_ms,
                'breach_id': breach_id,
                'name': line.get('scenario_name'),
                'user': user,
                'remarks': line.get('remarks', ''),
                'inundationmodel': inundation_model.id,
                'calcpriority': 20,
                'project_fk': project.id,
                # for boundary conditions
                'extwmaxlevel': waterlevel,
                'tpeak_ms': 0,
                'tstorm_ms': 0,
                'tstartbreach_ms': 0,
                'tdeltaphase_ms': 0,
                'extwbaselevel': waterlevel,
                'useManualInput': True,
                'waterlevelInput': "0,{0}".format(waterlevel),
                # for scenariobreach
                'externalwatermodel': externalwater_model.id,
                'widthbrinit': 10,
                'brdischcoef': 1,
                'brf1': 1.3,
                'brf2': 0.04,
                'bottomlevelbreach': max(breach.groundlevel,
                                         breach.canalbottomlevel) + 0.05,
                'ucritical': breach.defrucritical,
                'pitdepth': (breach.groundlevel-0.1),
                'tmaxdepth_ms': 3600000,

                # location cuttoffs
                # "id|action|tclose_ms,", # 1 = dicht, 2 = open
                'loccutoffs': ','.join(cutoff_str),

                # measures
                'measures': "",
            }

            requests.append(request)

        # create scenarios, after going through all rlines and check for as far as possible
        # if they are correct

        for request in requests:
            log.debug(request.POST)

            log.debug(service_save_new_scenario(request))

        log.info("END")
