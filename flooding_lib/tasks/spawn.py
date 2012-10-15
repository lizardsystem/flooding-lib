#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#*
#***********************************************************************
#*                      All rights reserved                           **
#*
#*
#*                                                                    **
#*
#*
#*
#***********************************************************************
#* Library    : <if this is a module, what is its name>
#* Purpose    : task 130: spawn and watch sobek.simulate.
#* Function   : main
#* Usage      : spawnsobek.py --help
#*
#* Project    : J0005
#*
#* $Id$
#*
#* $Name:  $
#*
#* initial programmer :  Mario Frasca
#* initial date       :  <yyyymmdd>
#* changed by         :  Alexandr Seleznev
#* changed at         :  20120601
#* changes            :  integration with django, pylint, pep8
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

"""this script executes simulate.exe and watches it until it ends or
times out.  please refer to LizardKadebreukRekencentrumSobekUitvoeren
for more details.
"""
import time
import os  # used throughout the code...
import logging
import subprocess
import threading
import re
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',)
log = logging.getLogger('nens')

from flooding_lib.models import Scenario, ResultType
from flooding_base.models import Setting

from django import db

from zipfile import ZipFile, ZIP_DEFLATED

default_sobek_locations = {
    'v2.09': 'sobek209/',
    'v2.10': 'sobek210/',
    'v2.11': 'sobek211/',
    'v2.12': 'sobek212/',
    }


def kill(pid):
    """kill function for Win32

    returns the return code of TerminateProcess or
    None in case of any failure"""
    try:
        import win32api
        handle = win32api.OpenProcess(1, False, pid)
        result = win32api.TerminateProcess(handle, -1)
        win32api.CloseHandle(handle)
    except:
        result = None
        pass
    return result


def watchdog(child, cmtwork_dir):
    """keep running until the simulate program has written to the
PLUVIUS1.rtn file, then kill the subprocess in case it's still
running.  does not return a value and does not check whether the
computation was successful.  here we are only interested in
terminating the subprocess when the computation is completed.
    """

    log.debug('inside watchdog cmtwork_dir %s, %s' % (type(cmtwork_dir), cmtwork_dir))
    # keep ignoring code 51 while warming up.  warming up ends as soon
    # as a different code appears or after 20 seconds.
    warming_up = 20

    file_to_monitor = os.path.join(cmtwork_dir, 'PLUVIUS1.rtn')
    last_stat = None
    text = ' 51\nstill warming up'

    while True:
        try:
            if warming_up:
                warming_up -= 1

            curr_stat = os.stat(file_to_monitor)
            if curr_stat != last_stat:
                # file changed
                log.debug("file changed")

                # reading it may cause an exception if 'simulate' is
                # still writing to the file.  no problem: we will
                # check at next step.
                input = open(os.path.join(cmtwork_dir, 'PLUVIUS1.rtn'))
                text = input.readlines()
                input.close()

                log.debug("%s" % text)

                # the assignment is at the end, so that it's not
                # performed in case of an exception.
                last_stat = curr_stat

            # test the status code on the first line
            result_code = int(text[0])
            if result_code != 51:
                warming_up = 0
            if result_code == 51 and warming_up:
                raise Exception("still warming up")

            if result_code != 0:
                log.warning('de berekening is met een fout beeindigd.')
                break

            # hij is of aan het rekenen of is hij klaar en de
            # berekening is gelukt.
            if text[1].find("Simulation finished succesfully"):
                log.info('de berekening lijkt (succesvol) afgelopen.')
                break

            # hij is nog aan het rekenen...
        except Exception, e:
            # er is een fout opgetreden.  bijvoorbeeld: het bestand
            # kon niet worden geopend, of het heeft niet voldoende
            # regels, of het is niet in het juiste formaat, in elk
            # geval ik negeer alle fouten in de hoop dat het bij een
            # volgende ronde wel lukt.
            log.debug("error in watchdog: (%s)..." % e)
            pass

        # keep the sleep time low, because threads can't be killed and
        # the main thread will be waiting for the watchdog.  a too
        # high sleep time will slow down exiting on completion
        log.debug('watchdog is about to go to sleep again')
        time.sleep(1)
        if child.poll() is not None:
            log.debug('watchdog thinks child already died')
            return

    log.debug("watchdog thinks the child ended but will kill it to make sure.")
    if kill(child.pid) is not None:
        log.debug("it was a good idea to kill the child.")
        output = open(os.path.join(cmtwork_dir, 'PLUVIUS1.rtn'), "w")
        output.write(" 51\nSimulation interrupted by spawning script\n\n")
        output.close()


def alarm_handler(timeout, child):
    count = 0
    while count < timeout:
        time.sleep(1)
        count += 1
        if child.poll() is not None:
            log.debug('alarm_handler thinks child already died')
            return
    log.debug("alarm_handler is about to kill the child")
    kill(child.pid)


def set_broker_logging_handler(broker_handler=None):
    """
    """
    if broker_handler is not None:
        log.addHandler(broker_handler)
    else:
        log.warning("Broker logging handler does not set.")


def perform_sobek_simulation(scenario_id,
                             sobek_project_directory,
                             sobek_program_root,
                             project_name='lizardkb',
                             timeout=288000):
    """task 130: perform_sobek_simulation
    """

    log.debug("step 0a: get settings")
    log.debug("sobek_project_directory: %s" % sobek_project_directory)
    log.debug("sobek_program_root: %s" % sobek_program_root)

    scenario = Scenario.objects.get(pk=scenario_id)

    sobek_location = os.path.join(
        sobek_program_root,
        default_sobek_locations[scenario.sobekmodel_inundation.sobekversion.name[:5]])
    #sobek_location = [d for d in sobek_location.split('/') if d]
    log.debug("sobek_location: %s" % sobek_location)
    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value
    source_dir = Setting.objects.get(key='SOURCE_DIR').value

    project_dir = os.path.join(sobek_location, sobek_project_directory)
    log.debug("project_dir: %s" % project_dir)
    log.debug("compute the local location of sobek files")
    # first keep all paths as lists of elements, will join them using
    # os.sep at the latest possible moment.
    case_1_dir = os.path.join(project_dir, '1')
    work_dir = os.path.join(project_dir, 'WORK')
    cmtwork_dir = os.path.join(project_dir, 'CMTWORK')

    output_dir_name = os.path.join(destination_dir, scenario.get_rel_destdir())
    model_file_location = os.path.join(
        destination_dir, scenario.result_set.get(resulttype=26).resultloc)

    log.debug("empty project_dir WORK & 1")
    for to_empty in [work_dir, case_1_dir, cmtwork_dir]:
        for root, dirs, files in os.walk(to_empty):
            for name in files:
                os.remove(os.path.join(root, name))

    log.debug("open the archived sobek model " + output_dir_name + "model.zip")

    input_file = ZipFile(model_file_location, "r")

    log.debug("unpacking the archived sobek model to project_dir WORK & 1")
    if not os.path.isdir(os.path.join(work_dir, 'grid')):
        os.makedirs(os.path.join(work_dir, 'grid'))
    if not os.path.isdir(os.path.join(case_1_dir, 'grid')):
        os.makedirs(os.path.join(case_1_dir, 'grid'))
    for name in input_file.namelist():
        content = input_file.read(name)
        temp = file(os.path.join(work_dir, name), "wb")
        temp.write(content)
        temp.close()
        temp = file(os.path.join(case_1_dir, name), "wb")
        temp.write(content)
        temp.close()

    settings_ini_location = os.path.join(
        source_dir,
        scenario.sobekmodel_inundation.sobekversion.fileloc_startfile)
    log.debug("copy from " + settings_ini_location + " to the CMTWORK dir")
    for name in ['simulate.ini', 'casedesc.cmt']:
        temp = file(os.path.join(cmtwork_dir, name), "w")
        content = file(os.path.join(settings_ini_location, name), "r").read()
        content = content.replace('lizardkb.lit', sobek_project_directory)
        content = content.replace('LIZARDKB.LIT', sobek_project_directory)
        temp.write(content)
        temp.close()

    program_name = os.path.join(sobek_location, "programs", "simulate.exe")
    configuration = os.path.join(cmtwork_dir, 'simulate.ini')
    log.debug("Close connection before spawning a subprocess.")
    db.close_connection()
    log.debug('about to spawn the simulate subprocess')
    cmd, cwd = [program_name, configuration], cmtwork_dir
    log.debug('command_list: %s, current_dir: %s' % (cmd, cwd))
    os.chdir(cwd)
    child = subprocess.Popen(cmd)

    log.debug('about to start the watchdog thread')
    log.debug('cmtwork_dir %s, %s' % (type(cmtwork_dir), cmtwork_dir))
    watchdog_t = threading.Thread(target=watchdog, args=(child, cmtwork_dir))
    watchdog_t.start()

    log.debug('about to start the alarm thread')
    alarm_t = threading.Thread(target=alarm_handler, args=(timeout, child,))
    alarm_t.start()

    log.debug("starting to wait for completion of subprocess")
    child.wait()

    log.debug('child returned')

    log.debug("open all destination zip files.")
    max_file_nr = {}
    min_file_nr = {}
    resulttypes = ResultType.objects.filter(program=1)

    matcher_destination = [(r.id, re.compile(r.content_names_re, re.I),
                            ZipFile(os.path.join(output_dir_name, r.name + '.zip'),
                                    mode="w", compression=ZIP_DEFLATED),
                            r.name)
                           for r in resulttypes if r.content_names_re is not None]

    # check the result of the execution
    saved = 0
    for filename in os.listdir(work_dir):
        log.debug("checking what to do with output file '%s'" % filename)
        for type_id, matcher, dest, _ in matcher_destination:
            if matcher.match(filename):
                log.debug("saving %s to %s" % (filename, dest.filename))
                content = file(os.path.join(work_dir, filename), 'rb').read()
                dest.writestr(filename, content)
                saved += 1
                try:
                    nr = int(''.join([i for i in filename[4:] if i.isdigit()]))
                    if nr > max_file_nr.setdefault(type_id, 0):
                        max_file_nr[type_id] = nr
                    if nr < min_file_nr.setdefault(type_id, 999):
                        min_file_nr[type_id] = nr
                except:
                    pass
                break

    log.debug("close all destination zip files")
    for _, _, dest, _ in matcher_destination:
        dest.close()

    log.debug("adding to the database what results have been computed...")
    for resulttype_id, _, _, name in matcher_destination:
        # table results
        result, new = scenario.result_set.get_or_create(
            resulttype=ResultType.objects.get(pk=resulttype_id))
        result.resultloc = os.path.join(
            scenario.get_rel_destdir(), name + '.zip')
        result.firstnr = min_file_nr.get(resulttype_id)
        result.lastnr = max_file_nr.get(resulttype_id)
        result.save()

    log.info("saved %d files" % saved)

    log.debug("check return code and return False if not ok")
    try:
        output = file(os.path.join(cmtwork_dir, 'PLUVIUS1.rtn'), "r")
        remarks = output.read()
    except:
        remarks = ' 51\nerror reading output file'

    remarks = 'rev: ' + __revision__ + "\n" + remarks

    log.info(remarks)
    log.debug("close db connection to avoid an idle process.")
    db.close_connection()
    successful = int(re.findall(r'\d+', remarks)[0]) == 0
    return successful
