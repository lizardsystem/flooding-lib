

def perform_task(scenario_id, tasktype_id, sequential, max_hours=72, hisssm_year=2008, hisssm_location='', tmp_directory='c:/temp'):
    "execute specific task"

    try:
        success_code = False
        error_messages = ''
        remarks = ''
        tmp_directory = os.path.join(tmp_directory,'%02d'%sequential)
        if tasktype_id == TASK_COMPUTE_SOBEK_MODEL_120:
            log.debug("execute TASK_COMPUTE_SOBEK_MODEL_120")
            from tasks import openbreach
            remarks = 'openbreach-' + openbreach.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = openbreach.compute_sobek_model(
                scenario_id, tmp_directory)

        elif tasktype_id == TASK_PERFORM_SOBEK_SIMULATION_130:
            log.debug("execute TASK_PERFORM_SOBEK_SIMULATION_130")
            from tasks import spawn
            remarks = 'spawn-' + spawn.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = spawn.perform_sobek_simulation(
                scenario_id, max_hours*3600, 'lzfl_%03d'%sequential)

        elif tasktype_id == TASK_SOBEK_PNG_GENERATION_150:
            log.debug("execute TASK_SOBEK_PNG_GENERATION_150")
            from tasks import png_generation
            remarks = 'png_generation-' + png_generation.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = png_generation.sobek(scenario_id, tmp_directory)

        elif tasktype_id == TASK_COMPUTE_RISE_SPEED_132:
            log.debug("execute TASK_COMPUTE_RISE_SPEED_132")
            from tasks import calculaterisespeed_132
            remarks = 'calculaterisespeed_132-' + calculaterisespeed_132.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = calculaterisespeed_132.perform_calculation(
                 scenario_id, tmp_directory, hisssm_year)

        elif tasktype_id == TASK_COMPUTE_MORTALITY_GRID_134:
            log.debug("execute TASK_COMPUTE_MORTALITY_GRID_134")
            from tasks import calculatemortalitygrid_134
            remarks = 'calculatemortalitygrid_134-' + calculatemortalitygrid_134.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = calculatemortalitygrid_134.perform_calculation(
                scenario_id, tmp_directory, hisssm_year)

        elif tasktype_id == TASK_SOBEK_PRESENTATION_GENERATION_155:
            log.debug("execute TASK_SOBEK_PRESENTATION_GENERATION_155")
            from tasks import presentationlayer_generation
            remarks = 'presentationlayer_generation-' + presentationlayer_generation.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = presentationlayer_generation.perform_presentation_generation(scenario_id)

        elif tasktype_id == TASK_HISSSM_SIMULATION_160:
            log.debug("execute TASK_HISSSM_SIMULATION_160")
            from tasks import hisssm_160
            remarks = 'hisssm_160-' + hisssm_160.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = hisssm_160.perform_HISSSM_calculation(
                scenario_id, hisssm_location, hisssm_year)

        elif tasktype_id == TASK_SOBEK_EMBANKMENT_DAMAGE_162:
            log.debug("execute TASK_SOBEK_EMBANKMENT_DAMAGE_162")
            from tasks import kadeschade_module
            remarks = 'kadeschade_module-' + kadeschade_module.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code, error_message = kadeschade_module.calc_damage(scenario_id)

        elif tasktype_id == TASK_HISSSM_PNG_GENERATION_180:
            log.debug("execute TASK_HISSSM_PNG_GENERATION_180")
            from tasks import png_generation
            remarks = 'png_generation-' + png_generation.__revision__ + ' uitvoerder: %02d/'%sequential
            success_code = png_generation.his_ssm(scenario_id, tmp_directory)
 
        elif tasktype_id == TASK_HISSSM_PRESENTATION_GENERATION_185:
            log.debug("execute TASK_HISSSM_PRESENTATION_GENERATION_185")
            from tasks import presentationlayer_generation
            remarks = 'presentationlayer_generation-' + presentationlayer_generation.__revision__ + ' uitvoerder: %02d/'%sequential
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

