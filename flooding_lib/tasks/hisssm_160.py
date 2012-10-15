#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#
# This file is part of Lizard Flooding 2.0.
#
# Lizard Flooding 2.0 is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lizard Flooding 2.0 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lizard Flooding 2.0.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright 2008, 2009 Mario Frasca
#
#***********************************************************************
# this script implements task 160: spawn and watch the HISSSM24
# program (has to be in ../bin/), that computes the damage in terms of
# money and human loss of the given scenario.  the scenario needs to
# have gone through SOBEK simulation.  task 160 waits for completion
# of the spawned program or times out.
#
# $Id$
#
# initial programmer :  Mario Frasca
# initial date       :  <yyyymmdd>
# changed by         :  Alexandr Seleznev
# changed at         :  20120601
# changes            :  integration with django, pylint, pep8
#***********************************************************************

__revision__ = "$Rev$"[6:-2]

from django import db
from zipfile import ZipFile, ZIP_DEFLATED
from flooding_lib.models import Scenario, Result, ResultType
from flooding_base.models import Setting

import os
import logging
import subprocess
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',)
log = logging.getLogger('nens')


def set_broker_logging_handler(broker_handler=None):
    """
    """
    if broker_handler is not None:
        log.addHandler(broker_handler)
    else:
        log.warning("Broker logging handler does not set.")

batchDotIni = """[Batch]
kenmerkModus=2

[Berekening]
berekeningkenmerk=%(kenmerk)s
scenariokenmerk=nens
datasetkenmerk=standaardmethode
modelkenmerk=standaardmethode

[Rapportage]
wegingsetkenmerk=standaardmethode
inflatiecijfer=2

[Rapportage.Rapport]
format=csv
path=results/txt

[Rapportage.Grids]
format=asc
path=results/grids

[scenario]
kenmerk=nens
locatie=..\demo\scenario1
waterdiepte.grid=dm1maxd0.asc
stijgsnelheid.grid=grid_dh.asc
stroomsnelheid.grid=dm1maxc0.asc
evacuatiefactor.waarde=0
hoogbouwveilig=true
gewenstprijspeil=%(year)s
"""


def cp(source, dest):
    in_file = file(source, "rb")
    out_file = file(dest, "wb")
    buf = in_file.read()
    out_file.write(buf)
    out_file.close()


def find_first(basedir='.', startswith='', endswith=''):
    """returns the first matching file
    """

    candidates = [i for i in os.listdir(basedir)
                  if i.lower().startswith(startswith) and i.lower().endswith(endswith)]
    if len(candidates) != 1:
        log.warn('more than one candidate %s*%s in %s directory!' % (startswith, endswith, basedir, ))
    log.debug("using first element without checking that there IS a first element.")
    return candidates[0]


def perform_HISSSM_calculation(scenario_id, tmp_location, timeout=0):

    log.debug("step 0a: get settings")
    scenario = Scenario.objects.get(pk=scenario_id)
    year = Setting.objects.get(key='YEAR').value
    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value

    log.debug("step 0c: get temp location: resetting to forward-slash")
    location = tmp_location.replace("\\", "/")
    if not location.endswith("/"):
        location += "/"

    log.debug("step 0d: find the name of the HISSSM executable")
    exefile = 'bin/' + find_first(location + 'bin/', startswith='hisssm', endswith='.exe')
    inifile = 'bin/' + find_first(location + 'bin/', startswith='hisssm', endswith='.ini')
    mdbfile = 'data/' + find_first(location + 'data/', startswith='ssm', endswith='_2000.mdb')

    log.debug("step 1a: cleaning up")
    for subdir, starts, ends in [('bin/', '', '.out',),
                                 ('data/berekening/', 'BER1', '',),
                                 ('data/berekening/grid/', 'BER1', '',),
                                 ('data/berekening/grid/', '', '.ASC',),
                                 ('demo/scenario1/', '', '.out',),
                                 ]:
        for filename in os.listdir(location + subdir):
            if filename.endswith(ends) and filename.startswith(starts):
                os.remove(os.path.join(location, subdir, filename))

    for root, dirs, files in os.walk(location + 'demo/scenario1/results/'):
        for filename in files:
            os.unlink(root + '/' + filename)
    try:
        os.removedirs(os.path.join(location, 'demo/scenario1/results/'))
    except:
        log.debug("results directory already not there")
        pass

    log.debug("step 1b: restoring initial HIS-SSM situation")
    for name in [inifile, mdbfile, 'data/basisdata/weg05.dbf']:
        cp(location + 'orig/' + name, location + name)

    log.debug("step 1c: get input data from filedatabase")

    for resulttype_id, names in [
        (1, ['dm1maxd0.asc']),
        (5, ['dm1maxc0.asc']),
        (19, ['grid_dh.asc']),
        ]:
        try:
            resultloc = scenario.result_set.get(resulttype=ResultType.objects.get(pk=resulttype_id)).resultloc
            input_file = ZipFile(os.path.join(destination_dir, resultloc), "r")

            for name in names:
                try:
                    content = input_file.read(name)
                    temp = file(os.path.join(location, 'demo/scenario1', name), "wb")
                    temp.write(content)
                    temp.close()
                except KeyError:
                    log.debug('file %s not found in archive' % name)
        except Result.DoesNotExist as e:
            log.error('inputfile of resulttype %i not found' % resulttype_id)
            log.error(','.join(map(str, e.args)))
            return False

    kenmerk = 'lizard_flooding'

    log.debug("step2: creating the batch.ini file")
    temp = file(os.path.join(location, 'demo/scenario1/batch.ini'), 'w')
    temp.write(batchDotIni % {'year': year, 'kenmerk': kenmerk})
    temp.close()

    log.debug("Close connection before spawning a subprocess.")
    db.close_connection()

    log.debug("step 3: run the external tool")
    log.debug("location = " + location)
    os.chdir(os.path.join(location, "demo"))
    command_line = ["../" + exefile, "scenario1/batch.ini"]
    log.debug('about to spawn the hisssm subprocess')
    child = subprocess.Popen(command_line)
    log.debug("starting to wait for completion of subprocess")
    child.wait()

    log.debug("step 4: retrieve the data from the files")
    temp = file(os.path.join(location, 'demo/scenario1/results/txt', kenmerk + '.csv'))
    for line in temp.readlines():
        if line.startswith("Schade;"):
            monetary = int(filter(str.isdigit, line))
        if line.startswith("Totaal aantal slachtoffers;"):
            casualties = int(filter(str.isdigit, line))
        if line.startswith("Aantal inwoners in overstroomd gebied;"):
            inhabitants = int(filter(str.isdigit, line))
    temp.close()

    log.debug("step 5: store the output files and the fact that they exist")

    for dirname, filename, zipfilename, resulttype, unit, value in [
        ('grids', 'slachtoffers-lizard_flooding.asc', 'gridcasualties.zip', 7, 'Pers', casualties),
        ('grids', 'schade-lizard_flooding.asc', 'griddamage.zip', 8, 'Euro', monetary),
        ('txt', 'lizard_flooding.csv', 'his-ssm-out.zip', 9, 'Pers', inhabitants)]:

        resultloc = os.path.join(scenario.get_rel_destdir(), zipfilename)

        content = file(os.path.join(location, 'demo/scenario1/results', dirname, filename), 'rb').read()
        output_file = ZipFile(os.path.join(destination_dir, resultloc), mode="w", compression=ZIP_DEFLATED)
        output_file.writestr(filename, content)
        output_file.close()

        result, new = scenario.result_set.get_or_create(
            resulttype=ResultType.objects.get(pk=resulttype))
        result.resultloc = resultloc
        result.unit = unit
        result.value = value
        result.save()

    log.debug("close db connection to avoid an idle process.")
    db.close_connection()
    log.debug("task finished")
    return True

# def main(options, args):
#     """translates options to connection + scenario_id, then calls perform_sobek_simulation
#     """
#     log.setLevel(options.loglevel)

#     from django.db import connection

#     perform_HISSSM_calculation(connection, options.hisssm_location, options.scenario, options.year, options.timeout)


# if __name__ == '__main__':

#     import logging
#     from optparse import OptionParser
#     parser = OptionParser()
#     parser.add_option('--hisssm-location', default='C:/Program Files/HIS-SSMv2.4/', help='the root of the his-ssm installation')

#     parser.add_option('--scenario', help='the ID of the scenario to be computed', type='int')
#     parser.add_option('--year', default=2008, help='the year of simulation data', type='int')

#     parser.add_option('--timeout', default=3600, type='int', help='timeout in seconds before killing HISSSM executable')
#     parser.add_option('--debug', help='be extremely verbose', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
#     parser.add_option('--quiet', help='be extremely silent', action='store_const', dest='loglevel', const=logging.WARNING)

#     (options, args) = parser.parse_args()
#     main(options, args)
