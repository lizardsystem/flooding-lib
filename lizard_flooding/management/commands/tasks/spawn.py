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
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

"""this script executes simulate.exe and watches it until it ends or
times out.  please refer to LizardKadebreukRekencentrumSobekUitvoeren
for more details.
"""
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',) 
log = logging.getLogger('nens')

if __name__ == '__main__':
    sys.path.append('..')
    
    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)

from lizard.flooding.models import Scenario, Result, ResultType, Task
from lizard.base.models import Setting

default_sobek_locations = {
    'v2.09': 'e:/sobek209/',
    'v2.10': 'e:/sobek210/',
    'v2.11': 'e:/sobek211/',
    'v2.12': 'e:/sobek212/',
    }

import time, os # used throughout the code...

def kill(pid):
    """kill function for Win32

    returns the return code of TerminateProcess or None in case of any failure"""
    try:
        import win32api
        handle = win32api.OpenProcess(1, False, pid)
        result = win32api.TerminateProcess(handle, -1)
        win32api.CloseHandle(handle)
    except:
        result = None
        pass
    return result

def watchdog(child, cmtwork_dir, ):
    """keep running until the simulate program has written to the
PLUVIUS1.rtn file, then kill the subprocess in case it's still
running.  does not return a value and does not check whether the
computation was successful.  here we are only interested in
terminating the subprocess when the computation is completed.
    """

    # keep ignoring code 51 while warming up.  warming up ends as soon
    # as a different code appears or after 20 seconds.
    warming_up = 20

    file_to_monitor = os.sep.join(cmtwork_dir+['PLUVIUS1.rtn'])
    last_stat = None
    text = ' 51\nstill warming up'

    while True:
        try:
            if warming_up: warming_up -= 1

            curr_stat = os.stat(file_to_monitor)
            if curr_stat != last_stat:
                # file changed
                log.debug("file changed")

                # reading it may cause an exception if 'simulate' is
                # still writing to the file.  no problem: we will
                # check at next step.
                input = open(os.sep.join(cmtwork_dir+['PLUVIUS1.rtn']))
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
        output = open(os.sep.join(cmtwork_dir+['PLUVIUS1.rtn']), "w")
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
    

def perform_sobek_simulation(conn, scenario_id, task_id, timeout, project_name='lizardkb'):
    """task 130: perform_sobek_simulation
    """

    log.debug("step 0a: get settings")
    
    scenario = Scenario.objects.get(pk=scenario_id)

    sobek_location = default_sobek_locations[scenario.sobekmodel_inundation.sobekversion.name[:5]]
    sobek_location = [d for d in sobek_location.split('/') if d]

    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value
    source_dir = Setting.objects.get(key='SOURCE_DIR').value

    project_dir = sobek_location + [project_name + '.lit']

    log.debug("compute the local location of sobek files")
    # first keep all paths as lists of elements, will join them using
    # os.sep at the latest possible moment.
    case_1_dir = project_dir + ['1']
    work_dir = project_dir + ['WORK']
    cmtwork_dir = project_dir + ['CMTWORK']

    output_dir_name = os.path.join(destination_dir, scenario.get_rel_destdir())
    model_file_location = os.path.join(destination_dir, scenario.result_set.get(resulttype=26).resultloc)

    log.debug("empty project_dir WORK & 1")
    for to_empty in [work_dir, case_1_dir, cmtwork_dir]:
        for root, dirs, files in os.walk(os.sep.join(to_empty)):
            for name in files:
                os.remove(os.path.join(root, name))

    log.debug("open the archived sobek model " + output_dir_name + "model.zip")

    from zipfile import ZipFile, ZIP_DEFLATED
    input_file = ZipFile(model_file_location, "r")

    log.debug("unpacking the archived sobek model to project_dir WORK & 1")
    if not os.path.isdir(os.sep.join(work_dir+['grid'])):
        os.makedirs(os.sep.join(work_dir+['grid']))
    if not os.path.isdir(os.sep.join(case_1_dir+['grid'])):
        os.makedirs(os.sep.join(case_1_dir+['grid']))
    for name in input_file.namelist():
        content = input_file.read(name)
        temp = file(os.sep.join(work_dir + [name]), "wb")
        temp.write(content)
        temp.close()
        temp = file(os.sep.join(case_1_dir + [name]), "wb")
        temp.write(content)
        temp.close()

    settings_ini_location = os.path.join(source_dir, scenario.sobekmodel_inundation.sobekversion.fileloc_startfile)
    log.debug("copy from "+settings_ini_location+" to the CMTWORK dir")
    for name in ['simulate.ini', 'casedesc.cmt']:
        temp = file(os.sep.join(cmtwork_dir + [name]), "w")
        content = file(settings_ini_location + name, "r").read()
        content = content.replace('lizardkb', project_name)
        content = content.replace('LIZARDKB', project_name)
        temp.write(content)
        temp.close()

    program_name = os.sep.join(sobek_location + ["programs", "simulate.exe"])
    configuration = os.sep.join(cmtwork_dir + ['simulate.ini'])

    log.debug('about to spawn the simulate subprocess')
    cmd, cwd = [program_name, configuration], os.sep.join(cmtwork_dir)
    log.debug('command_list: %s, current_dir: %s' % (cmd, cwd))
    import subprocess
    os.chdir(cwd)
    child = subprocess.Popen(cmd)

    log.debug('about to start the watchdog thread')
    import threading
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
    import re
    matcher_destination = [(r.id, re.compile(r.content_names_re, re.I), 
                            ZipFile(os.path.join(output_dir_name, r.name + '.zip'), 
                                    mode="w", compression=ZIP_DEFLATED), 
                            r.name) 
                           for r in resulttypes if r.content_names_re is not None]

    # check the result of the execution
    saved = 0
    for filename in os.listdir(os.sep.join(work_dir)):
        log.debug("checking what to do with output file '%s'" % filename)
        for type_id, matcher, dest, _ in matcher_destination:
            if matcher.match(filename):
                log.debug("saving %s to %s" % (filename, dest.filename))
                content = file(os.sep.join(work_dir + [filename]), 'rb').read()
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
        result, new = scenario.result_set.get_or_create(resulttype=ResultType.objects.get(pk=resulttype_id))
        result.resultloc =  os.path.join(scenario.get_rel_destdir(), name + '.zip')
        result.firstnr = min_file_nr.get(resulttype_id)
        result.lastnr = max_file_nr.get(resulttype_id)
        result.save() 
        

    log.info("saved %d files" % saved)

    log.debug("check return code and return False if not ok")
    try:
        output = file(os.sep.join(cmtwork_dir+['PLUVIUS1.rtn']), "r")
        remarks = output.read()
    except:
        remarks = ' 51\nerror reading output file'

    remarks = 'rev: ' + __revision__ + "\n" + remarks
    
    try:
        task = Task.objects.get(pk=task_id)
        task.remarks = remarks
        task.save()
        result = remarks.split('\n')[1:3] # the first two lines of the original content of PLUVIUS1
    except Exception, e:
        log.warning("error writing remarks to database")
        log.warning("%s" % e)
        result = [' 51', 'error writing remarks to database']
    #finally: is not present in python 2.4

    result[0] = int(result[0])
    return result

def main(options, args):
    """translates options to connection + scenario_id, then calls perform_sobek_simulation
    """
    
    log.setLevel(options.loglevel)

    from django.db import connection
    
    # the following will not work as the amount of parameters is not
    # correct.  but I do not know where to get the task_id from so I
    # will leave it as it is: not working...
    perform_sobek_simulation(connection, options.scenario, options.timeout) 

if __name__ == '__main__':

    import logging
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('--scenario', help='the ID of the scenario to be computed', type='int')

    parser.add_option('--timeout', default=3600, type='int', help='timeout in seconds before killing simulate.exe')
    parser.add_option('--debug', help='be extremely verbose', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    parser.add_option('--quiet', help='be extremely silent', action='store_const', dest='loglevel', const=logging.WARNING)

    (options, args) = parser.parse_args()
    main(options, args)
