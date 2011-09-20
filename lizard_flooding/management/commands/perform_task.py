import os
from optparse import make_option
import logging #, threading, time, datetime, random, math

from django.core.management.base import BaseCommand
from flooding import settings

log = logging.getLogger('nens.lizard.flooding.perform_task')

TASK_ADMIN_CREATES_SCENARIO_050   =  50
TASK_COMPUTE_SOBEK_MODEL_120      = 120
TASK_PERFORM_SOBEK_SIMULATION_130 = 130
TASK_COMPUTE_RISE_SPEED_132       = 132
TASK_COMPUTE_MORTALITY_GRID_134   = 134
TASK_SOBEK_PNG_GENERATION_150     = 150
TASK_HISSSM_SIMULATION_160        = 160
TASK_SOBEK_EMBANKMENT_DAMAGE_162  = 162
TASK_HISSSM_PNG_GENERATION_180    = 180
TASK_SOBEK_PRESENTATION_GENERATION_155  = 155
TASK_HISSSM_PRESENTATION_GENERATION_185 = 185


def perform_task(scenario_id, tasktype_id, worker_nr):
    """execute specific task
        scenario_id  = id of scenario
        tasktype_id  = id of tasktype (120,130,132)
        worker_nr = number of worker (1,2,3,4,5,6,7,8). Used for temp directory and sobek project.
    """

    #settings.py:
    hisssm_root = settings.HISSSM_ROOT
    sobek_program_root = settings.SOBEK_PROGRAM_ROOT
    sobek_project_root = settings.SOBEK_PROJECT_ROOT
    tmp_root = settings.TMP_ROOT

    tmp_directory = os.path.join(tmp_root, str(worker_nr))
    sobek_project_directory = os.path.join(sobek_project_root, 'lzfl_%03d'%worker_nr)    
    #settings van flooding
    max_hours = 72

    #settings van scenario:
    hisssm_year = 2008
    
    try:
        success_code = False
        error_messages = ''
        remarks = ''
        if tasktype_id == TASK_COMPUTE_SOBEK_MODEL_120:
            log.debug("execute TASK_COMPUTE_SOBEK_MODEL_120")
            from tasks import openbreach
            remarks = 'openbreach-' + openbreach.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = openbreach.compute_sobek_model(scenario_id,
                                                          tmp_directory)

        elif tasktype_id == TASK_PERFORM_SOBEK_SIMULATION_130:
            log.debug("execute TASK_PERFORM_SOBEK_SIMULATION_130")
            from tasks import spawn
            remarks = 'spawn-' + spawn.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = spawn.perform_sobek_simulation(scenario_id,
                                                          sobek_project_directory,
                                                          sobek_program_root)

        elif tasktype_id == TASK_SOBEK_PNG_GENERATION_150:
            log.debug("execute TASK_SOBEK_PNG_GENERATION_150")
            from tasks import png_generation
            remarks = 'png_generation-' + png_generation.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = png_generation.sobek(scenario_id,
                                                tmp_directory)

        elif tasktype_id == TASK_COMPUTE_RISE_SPEED_132:
            log.debug("execute TASK_COMPUTE_RISE_SPEED_132")
            from tasks import calculaterisespeed_132
            remarks = 'calculaterisespeed_132-' + calculaterisespeed_132.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = calculaterisespeed_132.perform_calculation(scenario_id,
                                                                      tmp_directory)

        elif tasktype_id == TASK_COMPUTE_MORTALITY_GRID_134:
            log.debug("execute TASK_COMPUTE_MORTALITY_GRID_134")
            from tasks import calculatemortalitygrid_134
            remarks = 'calculatemortalitygrid_134-' + calculatemortalitygrid_134.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = calculatemortalitygrid_134.perform_calculation(scenario_id,
                                                                          tmp_directory)

        elif tasktype_id == TASK_SOBEK_PRESENTATION_GENERATION_155:
            log.debug("execute TASK_SOBEK_PRESENTATION_GENERATION_155")
            from tasks import presentationlayer_generation
            remarks = 'presentationlayer_generation-' + presentationlayer_generation.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = presentationlayer_generation.perform_presentation_generation(scenario_id)

        elif tasktype_id == TASK_HISSSM_SIMULATION_160:
            log.debug("execute TASK_HISSSM_SIMULATION_160")
            from tasks import hisssm_160
            remarks = 'hisssm_160-' + hisssm_160.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = hisssm_160.perform_HISSSM_calculation(scenario_id,
                                                                 hisssm_root)

        elif tasktype_id == TASK_SOBEK_EMBANKMENT_DAMAGE_162:
            log.debug("execute TASK_SOBEK_EMBANKMENT_DAMAGE_162")
            from tasks import kadeschade_module
            remarks = 'kadeschade_module-' + kadeschade_module.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code, error_message = kadeschade_module.calc_damage(scenario_id)

        elif tasktype_id == TASK_HISSSM_PNG_GENERATION_180:
            log.debug("execute TASK_HISSSM_PNG_GENERATION_180")
            from tasks import png_generation
            remarks = 'png_generation-' + png_generation.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = png_generation.his_ssm(scenario_id, tmp_directory)
 
        elif tasktype_id == TASK_HISSSM_PRESENTATION_GENERATION_185:
            log.debug("execute TASK_HISSSM_PRESENTATION_GENERATION_185")
            from tasks import presentationlayer_generation
            remarks = 'presentationlayer_generation-' + presentationlayer_generation.__revision__ + ' uitvoerder: %02d/'%worker_nr
            success_code = presentationlayer_generation.perform_presentation_generation(scenario_id)

        else:
            log.warning("selected a '%d' task but don't know what it is" % tasktype_id)
            remarks = 'unknown task'

        return success_code, remarks, error_message


    except Exception, e:
        from sys import exc_info
        from traceback import format_tb
        (this_exctype, this_value, this_traceback) = exc_info()

        log.warning(''.join(['traceback: \n'] + format_tb(this_traceback)))
                    
        log.error("while executing task %s: '%s(%s)'" % 
                  (tasktype_id,  type(e), str(e)))

        return False, remarks, '%s(%s)'%(type(e),str(e))



class Command(BaseCommand):
    help = ("""\
uitvoerder.py [options]

for example:
bin/django perform_task --capabilities 120 --scenario 50 --worker_nr 1
""")

    option_list = BaseCommand.option_list + (
    make_option('--info', help='be sanely informative - the default', action='store_const', dest='loglevel', const=logging.INFO, default=logging.INFO),
    make_option('--debug', help='be verbose', action='store_const', dest='loglevel', const=logging.DEBUG),
    make_option('--quiet', help='log warnings and errors', action='store_const', dest='loglevel', const=logging.WARNING),
    make_option('--extreme-debugging', help='be extremely verbose', action='store_const', dest='loglevel', const=0),
    make_option('--silent', help='log only errors', action='store_const', dest='loglevel', const=logging.ERROR),

    make_option('--tasktype_id', help='tasks that uitvoerder must perform', default=120, type='int'),

    make_option('--scenario_id', help='scenarios', type='int', default=[-1, -1]),
    make_option('--worker_nr', help='use this if you need more than one uitvoerder on this workstation', type='int', default=1))

    def handle(self, *args, **options):
        perform_task(options['scenario_id'], options['tasktype_id'], options['worker_nr'])
