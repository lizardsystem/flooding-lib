import os
import logging  # , threading, time, datetime, random, math

from flooding_lib.models import Scenario

from django.conf import settings

log = logging.getLogger('flooding-lib.perform_task')

TASK_ADMIN_CREATES_SCENARIO_050 = 50
TASK_COMPUTE_SOBEK_MODEL_120 = 120
TASK_PERFORM_SOBEK_SIMULATION_130 = 130
TASK_COMPUTE_RISE_SPEED_132 = 132
TASK_COMPUTE_MORTALITY_GRID_134 = 134
TASK_SOBEK_PYRAMID_GENERATION_150 = 150
TASK_HISSSM_SIMULATION_160 = 160
TASK_SOBEK_EMBANKMENT_DAMAGE_162 = 162
TASK_SOBEK_EMBANKMENT_DAMAGE_WATERNET_164 = 164
TASK_HISSSM_PYRAMID_GENERATION_180 = 180
TASK_SOBEK_PRESENTATION_GENERATION_155 = 155
TASK_HISSSM_PRESENTATION_GENERATION_185 = 185
TASK_CALCULATE_STATISTICS = 190
TASK_GENERATE_EXPORT = 200  # See README.txt
TASK_GENERATE_DATA_EXPORT = 201  # See README.txt
TASK_PERFORM_3DI_SIMULATION_210 = 210  # See README.txt
TASK_3DI_PNG_GENERATION_220 = 220  # See README.txt
TASK_3DI_PNG_GENERATION_221 = 221
TASK_3DI_PNG_GENERATION_222 = 222


def update_scenario_status_cache(scenario_id):
    """
    Update the scenario's status_cache to CALCULATED.
    """
    scenario = Scenario.objects.get(pk=scenario_id)
    scenario.has_sobek_presentation = True
    scenario.save()
    scenario.update_status()


def perform_task(body, tasktype_id, worker_nr, broker_logging_handler=None):
    """
    execute specific task
    scenario_id  = id of scenario
    tasktype_id  = id of tasktype (120,130,132)
    worker_nr = number of worker (1,2,3,4,5,6,7,8). Used for temp
    directory and sobek project.
    broker_logging_handler = sends loggings to broker
    """
    scenario_type = body['scenario_type']
    scenario_id = body['scenario_id']

    #logging handler
    if broker_logging_handler is not None:
        log.addHandler(broker_logging_handler)
    else:
        log.warning("Broker logging handler does not set.")

    #settings.py:
    hisssm_root = settings.HISSSM_ROOT
    sobek_program_root = settings.SOBEK_PROGRAM_ROOT  # e: or c:
    #sobek_project_root = settings.SOBEK_PROJECT_ROOT
    tmp_root = settings.TMP_ROOT

    tmp_directory = os.path.join(tmp_root, str(worker_nr))
    if not os.path.exists(tmp_directory):
        os.mkdir(tmp_directory)

    sobek_project_directory = os.path.join(
         'lzfl_%03d.lit' % worker_nr)

    try:
        success_code = False
        error_message = ""
        remarks = ''
        if tasktype_id == TASK_COMPUTE_SOBEK_MODEL_120:
            log.debug("execute TASK_COMPUTE_SOBEK_MODEL_120")
            from flooding_lib.tasks import openbreach
            openbreach.set_broker_logging_handler(broker_logging_handler)
            remarks = ('openbreach-' + openbreach.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = openbreach.compute_sobek_model(scenario_id,
                                                          tmp_directory)

        elif tasktype_id == TASK_PERFORM_SOBEK_SIMULATION_130:
            log.debug("execute TASK_PERFORM_SOBEK_SIMULATION_130")
            from flooding_lib.tasks import spawn
            spawn.set_broker_logging_handler(broker_logging_handler)
            remarks = ('spawn-' + spawn.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = spawn.perform_sobek_simulation(
                scenario_id,
                sobek_project_directory,
                sobek_program_root)

        elif tasktype_id == TASK_SOBEK_PYRAMID_GENERATION_150:
            log.debug("execute TASK_SOBEK_PYRAMID_GENERATION_150")
            from flooding_lib.tasks import pyramid_generation
            pyramid_generation.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('pyramid_generation-' +
                       pyramid_generation.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = pyramid_generation.sobek(
                scenario_id, tmp_directory)

        elif tasktype_id == TASK_COMPUTE_RISE_SPEED_132:
            log.debug("execute TASK_COMPUTE_RISE_SPEED_132")
            from flooding_lib.tasks import calculaterisespeed_132
            calculaterisespeed_132.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('calculaterisespeed_132-' +
                       calculaterisespeed_132.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = calculaterisespeed_132.perform_calculation(
                scenario_id, tmp_directory)

        elif tasktype_id == TASK_COMPUTE_MORTALITY_GRID_134:
            log.debug("execute TASK_COMPUTE_MORTALITY_GRID_134")
            from flooding_lib.tasks import calculatemortalitygrid_134
            calculatemortalitygrid_134.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('calculatemortalitygrid_134-' +
                       calculatemortalitygrid_134.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = calculatemortalitygrid_134.perform_calculation(
                scenario_id, tmp_directory)

        elif tasktype_id == TASK_SOBEK_PRESENTATION_GENERATION_155:
            log.debug("execute TASK_SOBEK_PRESENTATION_GENERATION_155")
            from flooding_lib.tasks import presentationlayer_generation
            presentationlayer_generation.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('presentationlayer_generation-' +
                       presentationlayer_generation.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = (
                presentationlayer_generation.perform_presentation_generation(
                    scenario_id, tasktype_id))
            if success_code:
                update_scenario_status_cache(scenario_id)

        elif tasktype_id == TASK_HISSSM_SIMULATION_160:
            log.debug("execute TASK_HISSSM_SIMULATION_160")
            from flooding_lib.tasks import hisssm_160
            hisssm_160.set_broker_logging_handler(broker_logging_handler)
            remarks = ('hisssm_160-' + hisssm_160.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = hisssm_160.perform_HISSSM_calculation(scenario_id,
                                                                 hisssm_root)

        elif tasktype_id == TASK_SOBEK_EMBANKMENT_DAMAGE_162:
            log.debug("execute TASK_SOBEK_EMBANKMENT_DAMAGE_162")
            from flooding_lib.tasks import kadeschade_module
            kadeschade_module.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('kadeschade_module-' + kadeschade_module.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code, error_message = kadeschade_module.calc_damage(
                scenario_id)

        elif tasktype_id == TASK_SOBEK_EMBANKMENT_DAMAGE_WATERNET_164:
            log.debug("execute TASK_SOBEK_EMBANKMENT_DAMAGE_WATERNET_164")
            from flooding_lib.tasks import kadeschade_module_waternet
            kadeschade_module_waternet.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('kadeschade_module-' + kadeschade_module_waternet.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code, error_message = kadeschade_module_waternet.calc_damage(
                scenario_id)

        elif tasktype_id == TASK_HISSSM_PYRAMID_GENERATION_180:
            log.debug("execute TASK_HISSSM_PYRAMID_GENERATION_180")
            from flooding_lib.tasks import pyramid_generation
            pyramid_generation.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('pyramid_generation-' +
                       pyramid_generation.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = pyramid_generation.his_ssm(
                scenario_id, tmp_directory)

        elif tasktype_id == TASK_HISSSM_PRESENTATION_GENERATION_185:
            log.debug("execute TASK_HISSSM_PRESENTATION_GENERATION_185")
            from flooding_lib.tasks import presentationlayer_generation
            presentationlayer_generation.set_broker_logging_handler(
                broker_logging_handler)
            remarks = ('presentationlayer_generation-' +
                       presentationlayer_generation.__revision__ +
                       ' uitvoerder: %02d/' % worker_nr)
            success_code = (
                presentationlayer_generation.perform_presentation_generation(
                    scenario_id, tasktype_id))

        elif tasktype_id == TASK_CALCULATE_STATISTICS:
            from flooding_lib.tasks import calculate_scenario_statistics
            calculate_scenario_statistics.calculate_statistics(scenario_id)
            success_code = True  # In case of problems, an exception is raised

        elif tasktype_id == TASK_GENERATE_EXPORT:
            if scenario_type == 'flooding_exportrun':
                from flooding_lib.tasks import calculate_export_maps
                # Here scenario_id is an exportrun_id
                calculate_export_maps.calculate_export_maps(scenario_id)
                success_code = True  # In case of problems, an exception is raised
            else:
                log.error(
                    ('Task not performed, because scenario_type is "%s"'
                     ' (and not "flooding_exportrun")') %
                    scenario_type)
                success_code = False
        elif tasktype_id == TASK_GENERATE_DATA_EXPORT:
            if scenario_type == 'flooding_exportrun':
                from flooding_lib.tasks import calculate_export_data
                calculate_export_data.set_broker_logging_handler(
                    broker_logging_handler)
                # Here scenario_id is an exportrun_id
                calculate_export_data.calculate_export_data(scenario_id)
                success_code = True
            else:
                log.error(
                    ('Task not performed, because scenario_type is "%s"'
                     ' (and not "flooding_exportrun")') %
                    scenario_type)
                success_code = False
        elif tasktype_id == TASK_PERFORM_3DI_SIMULATION_210:
            log.debug("execute TASK_PERFORM_3DI_SIMULATION_210 %s=%r" % (scenario_type, scenario_id))
            from flooding_lib.tasks.threedi_210 import run_threedi_task
            run_threedi_task(scenario_id, scenario_type)
            success_code = True  # In case of problems, an exception is raised
        elif tasktype_id == TASK_3DI_PNG_GENERATION_220:
            log.debug("execute TASK_3DI_PNG_GENERATION_220 %s=%r" % (scenario_type, scenario_id))
            from flooding_lib.tasks.threedi_nc_220 import process_threedi_nc
            process_threedi_nc(scenario_id, scenario_type, with_region=True)
            success_code = True  # In case of problems, an exception is raised
        elif tasktype_id == TASK_3DI_PNG_GENERATION_221:
            log.debug("execute TASK_3DI_PNG_GENERATION_221 (detailed) %s=%r" % (scenario_type, scenario_id))
            from flooding_lib.tasks.threedi_nc_220 import process_threedi_nc
            process_threedi_nc(scenario_id, scenario_type, detailed=True, gridsize=0.5)
            success_code = True  # In case of problems, an exception is raised
        elif tasktype_id == TASK_3DI_PNG_GENERATION_222:
            log.debug("execute TASK_3DI_PNG_GENERATION_220 %s=%r" % (scenario_type, scenario_id))
            from flooding_lib.tasks.threedi_nc_220 import process_threedi_nc
            process_threedi_nc(scenario_id, scenario_type, with_region=False)
            success_code = True  # In case of problems, an exception is raised
        else:
            log.warning("selected a '%d' task but don't know what it is" %
                        tasktype_id)
            remarks = 'unknown task'

        return success_code, remarks, error_message

    except Exception, e:
        from sys import exc_info
        from traceback import format_tb
        (this_exctype, this_value, this_traceback) = exc_info()

        log.warning(''.join(['traceback: \n'] + format_tb(this_traceback)))

        log.error("while executing task %s: '%s(%s)'" %
                  (tasktype_id,  type(e), str(e)))

        return False, remarks, '%s(%s)' % (type(e), str(e))
