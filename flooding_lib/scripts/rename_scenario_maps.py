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
#* Library    : Presentation_shape_generation
#* Purpose : convert a sobekmodel and resultfiles (his-files) to a
#* Presentation_shape
#* Function   : Presentation_shape_generation.sobek/his_ssm
#*
#* Project    : Lizard-flooding v2.0
#*
#* $Id: presentation_shape_generation.py 7947 2009-09-07 08:23:36Z Bastiaan $
#*
#* initial programmer :  Bastiaan Roos
#* initial date       :  20090722
#
#**********************************************************************

__revision__ = "$Rev: 7947 $"[6:-2]

if __name__ == '__main__':
    import sys
    sys.path.append('..\\..')

    import settings

    from django.core.management import setup_environ
    setup_environ(settings)

    from flooding_lib.models import \
        Scenario, Region, \
        Result, ResultType

    import shutil
    import re

    from flooding_base.models import Setting
    import os

    source_dir = Setting.objects.get(key='source_dir').value
    dest_dir = Setting.objects.get(key='destination_dir').value
    presentation_dir = Setting.objects.get(key='presentation_dir').value

    import logging
    log = logging.getLogger('nens.web.tools')

    #settings
    #always_create_new_derivative = False
    #check_timestamp_original_sourcefile = False
    '''
    To do:
    get_or_create_presentation_sources:
    * his-files toevoegen
    * return aanpassen

    * PresentationShape maken (nu worden alleen de sources gemaakt).


    Later:
    * check of parameter aanwezig is in his-file
    * verkrijgen van animatie gegevens


    nog wat mee doen:
    * file_content = file_content.replace('\r\n', '\n')

    '''

    import sys
    if sys.version_info < (2, 5):
        print (
            "I think I need version python2.6 and I was called from %d.%d" %
            sys.version_info[:2])

    import logging

    log = logging.getLogger('nens.web.flooding.presentationlayer_generation')

    source_dir = '\\\\192.168.1.14\\BackupFlooding\\resultaten'
    dest_dir = '\\\\192.168.1.14\\BackupFlooding\\resultaten_new'

    for scenario in Scenario.objects.filter(
        migrated=None).exclude(id__in=[7007, 7006]):
        print "scenario: " + str(scenario.id)
        region = Region.objects.filter(breach__scenario=scenario)[0]
        #create directory
        new_scenario_dir = os.path.join(region.path, str(scenario.id)) + "\\"
        if not os.path.isdir(os.path.join(dest_dir, new_scenario_dir)):
            os.makedirs(os.path.join(dest_dir, new_scenario_dir))

        for result in scenario.result_set.all():
            # PROJECT KOALA
        #print "result: " + str(result.resulttype.id)
            try:
                if result.resulttype.id == 16:
                    if scenario.result_set.filter(resulttype=26).count() == 0:
                        source_filename = result.resultloc.replace(
                            'simulatie_rapport.zip', 'model.zip'
                            ).replace('/', '\\')
                        project_dir = re.match(r'(\d+\\)+', source_filename)
                        new_filename = source_filename.replace(
                            project_dir.group(), new_scenario_dir)

                        source = os.path.join(source_dir, source_filename)
                        dest = os.path.join(dest_dir, new_filename)
                        #print "new model - move %s to %s"%(source, dest)
                        shutil.move(source, dest)

                        Result.objects.create(
                            scenario=scenario,
                            resulttype=ResultType.objects.get(pk=26),
                            resultloc=new_filename)
            except AttributeError, e:
                print "error: %s" % e
            except IOError, e:
                print "can't find model of scenario %i: %s" % (scenario.id, e)
                result.unit = 'error'
                result.save()

            try:
                if not (result.resultloc == None or result.resultloc == ""):
                    #get new file name
                    source_filename = result.resultloc.replace('/', '\\')
                    project_dir = re.match(r'(\d+\\)+', source_filename)
                    new_filename = source_filename.replace(
                        project_dir.group(), new_scenario_dir)

                    source = os.path.join(source_dir, source_filename)
                    dest = os.path.join(dest_dir, new_filename)
                    #print "move %s to %s"%(source, dest)
                    shutil.move(source, dest)

                    result.resultloc = new_filename
                    result.save()
            except AttributeError, e:
                print "error: %s" % e
            except IOError, e:
                print ("can't find resulttype %i of scenario %i: %s" %
                       (result.resulttype.id, scenario.id, e))
                result.unit = 'error'
                result.save()

            try:
                if not (result.resultpngloc == None or
                        result.resultpngloc == ""):
                    #get new file name
                    source_filename = result.resultpngloc.replace('/', '\\')
                    project_dir = re.match(r'(\d+\\)+', source_filename)
                    new_filename = source_filename.replace(
                        project_dir.group(), new_scenario_dir)

                    source = os.path.join(
                        source_dir, os.path.split(source_filename)[0])
                    dest = os.path.join(
                        dest_dir, os.path.split(new_filename)[0])
                    #print "------------move %s to %s"%(source, dest)
                    shutil.move(source, dest)

                    result.resultpngloc = new_filename
                    result.save()
            except AttributeError, e:
                print "error: %s" % e
            except IOError, e:
                print ("can't find resulttype %i of scenario %i: %s" %
                       (result.resulttype.id, scenario.id, e))
                result.unit = 'error-png'
                result.save()

            #create model result

        scenario.migrated = True
        scenario.save()

#voor alle scenario's:
#- resultaten tabel aanpassen
#- naam
#- scenario
#
#
#
#
#
#
#
#
#
#
#
#
#
