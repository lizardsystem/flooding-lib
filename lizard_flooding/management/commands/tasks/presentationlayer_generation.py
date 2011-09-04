#!/usr/bin/env python
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
#* Purpose    : convert a sobekmodel and resultfiles (his-files) to a Presentation_shape
#* Function   : Presentation_shape_generation.sobek/his_ssm
#*               
#* Project    : Lizard-flooding v2.0
#*  
#* $Id: presentation_shape_generation.py 8118 2009-09-29 15:54:56Z JanMaarten $
#*
#* initial programmer :  Bastiaan Roos
#* initial date       :  20090722
#
#**********************************************************************

'''
To do:
* check of parameter aanwezig is in his-file
nog wat mee doen:
* file_content = file_content.replace('\r\n', '\n')
'''

__revision__ = "$Rev: 8118 $"[6:-2]

import sys
import logging

log = logging.getLogger('nens.web.flooding.presentationlayer_generation') 

if sys.version_info < (2, 5):
    message =  "I think I need version python2.6 and I was called from %d.%d" % sys.version_info[:2]
    print message
    log.error(message)
    
if __name__ == '__main__':
    sys.path.append('..')
    
    import lizard.settings
    from django.core.management import setup_environ
    setup_environ(settings)     

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.contrib.gis.geos import Point

from lizard.flooding.models import Project, UserPermission, \
    ProjectGroupPermission, Scenario, Region, RegionSet, Breach, \
    ScenarioCutoffLocation, \
    ScenarioBreach, Result, ResultType, Task, TaskType, \
    ExternalWater, CutoffLocation, CutoffLocationSet, SobekModel, \
    Scenario_PresentationLayer, ResultType_PresentationType
from lizard.presentation.models import SourceLinkType, SourceLink, \
    PresentationSource, PresentationType, PresentationLayer, \
    PresentationShape, PresentationValueTable, PresentationGrid, Animation, Field
from lizard.base.models import Setting

from nens import sobek
from nens.mock import Stream
from nens.sobek import HISFile
from osgeo import ogr, osr
from shutil import copyfile, copytree, rmtree
from zipfile import ZipFile, ZIP_DEFLATED

import Image
from lizard import settings
import os, datetime

source_dir = Setting.objects.get( key = 'source_dir' ).value
dest_dir = Setting.objects.get( key = 'destination_dir' ).value
presentation_dir = Setting.objects.get( key = 'presentation_dir' ).value

def rel_path(loc):
    return loc.lstrip('\\').lstrip('/')



def get_or_create_model_shapefile_def(model_loc, output_dir, generate, srid, check_source_file_last_modified = None):
    '''
    input:
        model_loc: name of directory or zipfile of model (recognize .zip)
        output_dir: output directory of shapefiles
        generate: dict with sources to generate
        srid
        
        return:
            generated files
            source date
    '''
    log.debug('!!!get_or_create_model_shapefile_def')
    
    #check source
    if not os.path.isfile(str(model_loc)) and not os.path.isdir(str(model_loc)):
        log.warning('source file is missing. ' + model_loc)
        return (False, None, None,  )

    if model_loc[-3:].lower() == 'zip':
        log.debug('read model from zipfile: ' + str(model_loc))
        zip_file = ZipFile(model_loc, "r")
        sobek_gr = Stream(zip_file.read('network.gr').replace('\r\n', '\n'))
        sobek_struc = Stream(zip_file.read('network.st'))
        source_file_last_modified = datetime.datetime.fromtimestamp(os.stat(str(model_loc))[8])
        zip_file.close()   
    else:  
        log.debug('read model from directory: ' + str(model_loc))
        sobek_gr = open( os.path.join(model_loc, 'network.gr') )
        sobek_struc = open( os.path.join(model_loc, 'network.st') )
        source_file_last_modified = datetime.datetime.fromtimestamp(os.stat(os.path.join(str(model_loc), 'network.gr'))[8])

    source_up_to_date = False
    log.debug('in db origin date is ' + str(check_source_file_last_modified))
    log.debug('file date is ' + str(source_file_last_modified) )   
    if check_source_file_last_modified and check_source_file_last_modified >= source_file_last_modified:
        log.info('source file is still up to date')
        source_up_to_date = True
        

    #check output
    log.debug('output dir for shapefile is ' + output_dir)
    if not os.path.isdir( output_dir ):
        log.info('create output dir' + output_dir)
        os.makedirs( output_dir )


    shapefile_name = {}  
    for type in ['nodes', 'branches', 'structures']:
        shapefile_name[type] = os.path.join(output_dir, type + '.shp')
        if generate[type] and os.path.isfile(shapefile_name[type]):
            if source_up_to_date:
                log.info('output for ' + type + ' exist and is up to date.')
                generate[type] = False
            else:
                log.info('output for ' + type + ' exist and is not up to date, or recreation is needed. Remove previous output.' )
                os.remove(shapefile_name[type])
                os.remove(shapefile_name[type].replace('.shp','.shx'))
                os.remove(shapefile_name[type].replace('.shp','.dbf'))
                os.remove(shapefile_name[type].replace('.shp','.prj'))  

    node_array = []
    branch_array = []
    node = {}
    node_dict = {}


    #start with reading source files    
    if generate['nodes'] or generate['branches'] or generate['structures']:
        log.debug('read locations of nodes and branches')
        pool = sobek.File(sobek_gr)

        #original SRS
        oSRS=ogr.osr.SpatialReference()
        
        # warning oSRS.ImportFromEPSG(28992) gives wrong string '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.387638888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +no_defs '
        oSRS.ImportFromProj4("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs" )
        #target SRS
        tSRS=ogr.osr.SpatialReference()
        tSRS.ImportFromEPSG(900913)
        poCT=ogr.osr.CoordinateTransformation(oSRS,tSRS)



        for candidate_grid in pool['GRID']:
            branch_id = candidate_grid['id'][0]
            table = candidate_grid['TBLE'][0]
            for row_no in range(table.rows()):
                node_id = table[row_no,3]
                #check if node is not already in dict
                if not node.has_key(node_id):
                    node[node_id] = True
                    pnt=poCT.TransformPoint(table[row_no,5],table[row_no,6],0.)
                    node_array.append({'id':node_id,'type':0,'x':int(pnt[0]),'y':int(pnt[1])})
                    node_dict[node_id] = {'id':node_id,'type':0,'x':int(pnt[0]),'y':int(pnt[1])}
             
                sub_branch_id = table[row_no,4]
                if (row_no != range(table.rows()) and sub_branch_id != ''):
                    branch_array.append({'id':sub_branch_id,'branch_id':branch_id,'dist_from':table[row_no,0], 'dist_to': table[row_no+1,0], 'type':0,'to':table[row_no+1,3],'from':table[row_no,3]})
        del pool
        #start generating shapefiles
        if generate['nodes']:
            log.info('generate shapefile for nodes')
            #make shapefile for nodes
            # Create the file object, a layer, and an attribute
            t_srs = osr.SpatialReference()
            t_srs.SetFromUserInput('900913')
            drv = ogr.GetDriverByName('ESRI Shapefile')
            ds = drv.CreateDataSource( str(shapefile_name['nodes']))
            
            layer = ds.CreateLayer(ds.GetName(), geom_type = ogr.wkbPoint, srs = t_srs)
            layer.CreateField(ogr.FieldDefn('id', ogr.OFTString))
            layer.CreateField(ogr.FieldDefn('type', ogr.OFTInteger))
            
            # Could loop the following over some number of features
            geom = ogr.Geometry(type=ogr.wkbPoint)   
            fid = 0
                
            for node in node_array:
                geom.SetPoint(0,node['x'],node['y'])
                feat = ogr.Feature(feature_def=layer.GetLayerDefn())
                feat.SetGeometry(geom)
                feat.SetFID(fid)
                feat.SetField('id', node['id'])
                feat.SetField('type', node['type'])
                layer.CreateFeature(feat)
               
                fid = fid + 1
            
            log.debug('nr of nodes '+ str(fid))
            layer.SyncToDisk()
            # Clean up
            ds.Destroy()
            
        if generate['branches']:
            log.info('generate shapefile for breaches')
            #make shapefile for branches
            # Create the file object, a layer, and an attribute
            t_srs = osr.SpatialReference()
            t_srs.SetFromUserInput('900913')
            drv = ogr.GetDriverByName('ESRI Shapefile')
            dsb = drv.CreateDataSource( str(shapefile_name['branches']))
            
            layerb = dsb.CreateLayer(dsb.GetName(), geom_type = ogr.wkbLineString, srs = t_srs)
            layerb.CreateField(ogr.FieldDefn('id', ogr.OFTString))
            layerb.CreateField(ogr.FieldDefn('type', ogr.OFTInteger))
            
            fid = 0

            for branch in branch_array:
                line = ogr.Geometry(type=ogr.wkbLineString) 
                line.AddPoint(node_dict[branch['from']]['x'],node_dict[branch['from']]['y'])
                line.AddPoint(node_dict[branch['to']]['x'],node_dict[branch['to']]['y'])
                feat = ogr.Feature(feature_def=layerb.GetLayerDefn())
                feat.SetGeometry(line)
                feat.SetFID(fid)
                feat.SetField('id', branch['id'])
                feat.SetField('type', branch['type'])
                feat.SetField('from', branch['from'])        
                feat.SetField('to', branch['to'])     
                layerb.CreateFeature(feat)
                fid = fid + 1
            
            log.debug('nr of branches '+ str(fid))
            layerb.SyncToDisk()
            # Clean up
            dsb.Destroy()

    if generate['structures']:
        log.debug('read locations of structures')
        #read extra sources for structures
        pool = sobek.File(sobek_struc)
        struc_array = []
        for candidate in pool['STRU']:
            struc = {}
            struc['id'] = candidate['id'][0]
            if candidate.has_key('nm'):
                struc['name'] = candidate['nm'][0]
            else:
                struc['name'] = '-'
            struc['branch_id'] = candidate['ci'][0]
            struc['dist'] = candidate['lc'][0]
            struc['type'] = -1

            location_found = False
            for branch in branch_array:
                if branch['branch_id'] == struc['branch_id'] and struc['dist'] >= branch['dist_from'] and struc['dist'] < branch['dist_to']:
                    struc['x'] = (node_dict[branch['from']]['x'] + node_dict[branch['to']]['x'])/2
                    struc['y'] = (node_dict[branch['from']]['y'] + node_dict[branch['to']]['y'])/2                    
                    location_found = True
                    break

            if location_found == False:
                log.warning('structure location not found for ' + str(struc))
                struc['x'] = 0
                struc['y'] = 0
            
            if struc['id'][:4] == 'lkb_' or struc['id'][:6] == 'c_lkb_' or struc['name'][:4] == 'lkb_':
                struc['origin'] = 1
            else:
                struc['origin'] = 0

            struc_array.append(struc)
 
        #make shapefile for structures
        t_srs = osr.SpatialReference()
        t_srs.SetFromUserInput('900913')
        drv = ogr.GetDriverByName('ESRI Shapefile')
        log.info('create shapefile ' + shapefile_name['structures'])
        ds = drv.CreateDataSource( str(shapefile_name['structures']))
        
        layer = ds.CreateLayer(ds.GetName(), geom_type = ogr.wkbPoint, srs = t_srs)
        layer.CreateField(ogr.FieldDefn('id', ogr.OFTString))
        layer.CreateField(ogr.FieldDefn('type', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('origin', ogr.OFTInteger))
        
        # Could loop the following over some number of features
        geom = ogr.Geometry(type=ogr.wkbPoint)   
        fid = 0
            
        for node in struc_array:
            geom.SetPoint(0,node['x'],node['y'])
            feat = ogr.Feature(feature_def=layer.GetLayerDefn())
            feat.SetGeometry(geom)
            feat.SetFID(fid)
            feat.SetField('id', node['id'])
            feat.SetField('type', node['type'])
            feat.SetField('origin', node['origin'])
            layer.CreateFeature(feat)
            feat.Destroy()
            fid = fid + 1
        
        log.debug('nr of structures '+ str(fid))
        layer.SyncToDisk()
        # Clean up
        ds.Destroy()
        del struc_array
        del pool

    del node_array 
    del branch_array 
    del node 
    del node_dict 

    return (True, shapefile_name, source_file_last_modified, )

def get_or_create_geo_presentation_source(scenario, pt, check_timestamp_original_sourcefile):
    '''
        create PresentationSource objects for given Flooding.Scenario and PresentationType
        input:
            scenario: Flooding.Scenario object
            pt: PresentationType object
            check_timestamp_original_sourcefile: check if shapefile is still up to date
        output:
            .....

        if there are no Results to fill the presentationLayer, this function return False
        In case of an error, an exeption is thrown. 
    '''
    log.debug('!!!get_or_create_geo_presentation_source')
    
    #get source model info and determine destination
    if pt.generation_geo_source == 'scenario_model':
        log.debug('use model of scenario')
        mod = scenario.result_set.get(resulttype = 16 )
        resultloc = mod.resultloc.replace('\\', '/')
        model_location = os.path.join(dest_dir, resultloc.replace('simulatie_rapport.zip', 'model.zip'))
        link_name = 'flooding_scenario_model'
        link_id = str(scenario.id)
        destination = os.path.join('flooding', 'scenario', str(scenario.id))
        if scenario.sobekmodel_inundation:
            model_srid = scenario.sobekmodel_inundation.model_srid
        else:
            model_srid = 28992 #assume this is a dutch model
    elif pt.generation_geo_source in ['extw_model','inundation_model']:
        if pt.generation_geo_source == 'extw_model':
            log.debug('use model of external water')
            sb = scenario.scenariobreach_set.get()
            if not sb.sobekmodel_externalwater:
                log.debug('scenario has no extw model')
                return (False, None, None, ) 
            model = sb.sobekmodel_externalwater
            link_name = 'flooding_extw_model'
        elif pt.generation_geo_source == 'inundation_model':
            log.debug('use model of inundation area')
            model = scenario.sobekmodel_inundation
            link_name = 'flooding_inundation_model'
        link_id = str(model.id)
        project_fileloc = model.project_fileloc.replace('\\', '/')
        model_location =  os.path.join(source_dir, project_fileloc, str(model.model_case))
        model_srid = model.model_srid
        destination = os.path.join('flooding', 'model', str(model.id))
    else:
        log.error('source model not supported')
        return (False, None, None, )

    #determine which shapefiles are desired
    generate_parts = {'nodes':False, 'branches':False, 'structures':False }
    for part in pt.generation_geo_source_part.split(','):
        if part in ['nodes', 'branches']:
            #if generate nodes, branches is almost always also needed. So create both at the same time to reduce creation time 
            generate_parts['nodes'] = True
            generate_parts['branches'] = True
        elif part == 'structures':
            generate_parts['structures'] = True
   
    #check if shape or shapefile already exist and create presentationsources
    link_type_model, _ = SourceLinkType.objects.get_or_create(name=link_name)
    source_link = {}
    source = {}
    source_new = {}
    date_origin = None
    for part in generate_parts:
        if generate_parts[part] == True:
            source_link[part], new = SourceLink.objects.get_or_create(link_id = link_id, sourcelinktype = link_type_model, type= 'shapefile_' + part )
            source[part], source_new[part]  = source_link[part].presentationsource.get_or_create(type = PresentationSource.SOURCE_TYPE_SHAPEFILE)
            
            if not source_new[part]:
                #shapefile is generated before. get some information to check if file is still up to date
                if date_origin == None or date_origin  > source[part].t_origin:
                    date_origin  = source[part].t_origin

    #make shapefiles
    successful, shapefiles, date_origin_new = get_or_create_model_shapefile_def(model_location, os.path.join(presentation_dir, destination), generate_parts, model_srid, date_origin)

    if not successful:
        for part in generate_parts:
            if generate_parts[part] == True:
                source_link[part].delete()
                source[part].delete()
                source[part] = None
        return (False, None, None, )

    if date_origin == None or date_origin < date_origin_new:
        log.info('origin is new, files updated')
        files_updated = True
    else:
        files_updated = False
        
    new = False
    for part in generate_parts:
        if generate_parts[part] == True:
            if source_new[part] or files_updated:
                new = True
                source_link[part].save()
                source[part].t_origin = date_origin_new
                source[part].t_source = datetime.datetime.now()
                source[part].file_location = shapefiles[part].replace( presentation_dir + '\\', '')
                source[part].save()

    return (True, source, new, )

def get_or_create_value_presentation_source(scenario, pt, get_animation_info, check_timestamp_original_sourcefile):
    '''
        create PresentationSource objects for given Flooding.Scenario and PresentationType
        input:
            scenario: Flooding.Scenario object
            pt: PresentationType object
            check_timestamp_original_sourcefile
        output:
            source object

        if there are no Results to fill the presentationLayer, this function throws an exception
        In case of an error, an exeption is thrown. 
    '''
    log.debug('!!!get_or_create_value_presentation_source')

    try:
        animation = {}

        result = scenario.result_set.get(resulttype__presentationtype = pt)

        link_type, _ = SourceLinkType.objects.get_or_create(name='flooding_scenario_value')
        source_link, new = SourceLink.objects.get_or_create(link_id=str(scenario.id), sourcelinktype = link_type, type= 'fl_rlt_' + str(result.id)  )
        source, new  = source_link.presentationsource.get_or_create(type = PresentationSource.SOURCE_TYPE_ZIPPED_HISFILE)

        if new or source.file_location is None:
            new = True
        elif not os.path.isfile(os.path.join(presentation_dir, rel_path(source.file_location))):
            new = True

                

        #source
        resultloc = result.resultloc.replace('\\', '/')
        source_file_name = os.path.join(dest_dir, resultloc)
        if check_timestamp_original_sourcefile and not new:
            log.debug('check timestamps')
            if os.path.isfile(source_file_name):
                source_file_last_modified = datetime.datetime.fromtimestamp(os.stat(str(source_file_name))[8])
                #adding timestamps where this was not filled before
                if source.t_origin == None or source.t_source == None:
                    source.t_origin = source_file_last_modified
                    source.t_source = datetime.datetime.now()
                    source.save()
                elif (source_file_last_modified > source.t_origin):
                    log.info('source file has changed, recreate')
                    new = True

        output_dir_name =  os.path.join('flooding', 'scenario', str(scenario.id))
        filename = source_file_name.replace('\\','/').split('/')[-1]
        output_file_name = os.path.join(output_dir_name, filename)
        
        if new:
            log.debug('copy file')
            #output
            output_path = os.path.join(presentation_dir, output_dir_name)
            if not os.path.isdir( output_path ):
                os.makedirs( output_path )

            destination_file_name = os.path.join(presentation_dir, output_file_name)
            log.debug('source file is ' + str(source_file_name))
            log.debug('destination is '+str(destination_file_name))

            try:
                if filename[-3:].lower() == 'zip':
                    copyfile(source_file_name, destination_file_name )
                else:
                    dest = ZipFile(str(destination_file_name)[:-3] + '.zip', 
                                   mode="w", compression=ZIP_DEFLATED)
                    dest.writestr(filename, file(source_file_name, 'rb').read() )
                    dest.close()

                source.file_location = output_file_name
                source.t_original = datetime.datetime.fromtimestamp(os.stat(str(source_file_name))[8])
                source.t_source = datetime.datetime.now()
                source.save()
                get_animation_info =True

            except IOError, e:
                source.delete()
                print 'error creating source'
                print str(e)
                raise IOError(e)

        if get_animation_info:
            log.debug('get animation information')
            zip_name = os.path.join(presentation_dir, output_file_name)
            input_file = ZipFile(zip_name, "r")
            his = HISFile(Stream(input_file.read(input_file.filelist[0].filename)))
            input_file.close()
                
            delta = (his.get_datetime_of_timestep(1) - his.get_datetime_of_timestep(0))
            animation['delta_timestep'] = delta.days + float(delta.seconds)/(24*60*60)
            animation['firstnr'] = 0
            animation['lastnr'] = his.size()-1
            animation['startnr'] = 0
    except Exception, e:
        log.error('error generation value source')
        log.error(e)
        return False, None, None, None

    return True, source, animation, new  

def get_or_create_shape_layer(scenario, pt, only_geom):
    log.debug('!!!get_or_create_shape_layer')

    pl, pl_new= PresentationLayer.objects.get_or_create(presentationtype = pt,scenario_presentationlayer__scenario = scenario )
    if pl_new:
         Scenario_PresentationLayer.objects.create(scenario = scenario, presentationlayer = pl)

    ps, ps_new = PresentationShape.objects.get_or_create(presentationlayer = pl)
    get_animation_info = False
    try:
        if not only_geom:
            if not Animation.objects.filter(presentationlayer = pl).count() > 0:
                get_animation_info = True
            value_successful, value_source, animation, value_new = get_or_create_value_presentation_source(scenario, pt, get_animation_info , not ps_new)

            if not animation == None and not animation == {}:
                log.debug('save animation ' + str(animation))
                #animation['presentationlayer'] = pl
                anim, new = Animation.objects.get_or_create(presentationlayer = pl, defaults = animation)
                if new:
                    log.debug('animation is new')
                anim.save()
            if value_new:
                log.debug('value source is new')
                  
        else:
            value_successful = False
        geo_successful, geo_source, geo_new = get_or_create_geo_presentation_source(scenario, pt, not ps_new)
        if geo_new:
            log.debug('geo source is new')
    except IOError, e:
        log.warning('error creating source, file error')
        log.warning(e)
        if pl_new:
            pl.delete()
        return False
    except Result.DoesNotExist, e:
        log.warning('error creating source, data not exist')
        log.warning(e)
        pl.delete()
        return False
    except ScenarioBreach.DoesNotExist, e:
        log.warning('error creating source, data not exist')
        log.warning(e)
        pl.delete()
        return False
        
    if value_successful and geo_successful or only_geom and geo_successful:
        ps.geo_source = geo_source[pt.generation_geo_source_part.split(',')[0]]
        if ( not only_geom):
            ps.value_source = value_source
        ps.save()
    else:
        pl.delete()
        return False

    return True


def get_or_create_pngserie_with_defaultlegend_from_old_results(scenario, pt):
    log.debug('!!!get_or_create_pngserie_with_defaultlegend_from_old_results')
   

    result = Result.objects.filter(scenario = scenario, resulttype__resulttype_presentationtype__presentationtype = pt)

    if result.count() > 0:
        #check if layer is already there
        result = result[0]
        log.info('result found')
        
        pl, pl_new= PresentationLayer.objects.get_or_create(presentationtype = pt, scenario_presentationlayer__scenario = scenario, defaults = {"value": result.value} )
        if pl_new:
            Scenario_PresentationLayer.objects.create(scenario = scenario, presentationlayer = pl)
            log.info("pl_new id: " + str(pl.id))

        pl.value = result.value
        pl.save()

    
        
        try:
            log.info(result.resultpngloc)
            if result.resultpngloc is not None:
                log.debug('read grid information from pgw en png file!')
                resultpngloc = result.resultpngloc.replace('\\', '/')
                png_name = os.path.join(dest_dir, resultpngloc)
    
                if result.resulttype.overlaytype == 'ANIMATEDMAPOVERLAY':
                    numberstring = '%4i' % result.firstnr
                    numberstring = numberstring.replace(" ","0")
                    png_name = png_name.replace('####',numberstring)
    
                pgw_name = png_name.replace(".png", ".pgw")
                pgwfile = open(pgw_name, 'r')
                pgwfields = pgwfile.readlines()
                pgwfile.close()
                gridsize, a, b, c, west, north = [float(s) for s in pgwfields]
    
                picture = Image.open( png_name )
                width, height = picture.size
                east = west +  width * gridsize
                south = north - height * gridsize
                
                old_file = resultpngloc.split('/')
                output_dir_name = os.path.join('flooding','scenario', str(scenario.id), old_file[-2])
                output_file_name = os.path.join(output_dir_name, old_file[-1])
                
                s_dir = os.path.join(dest_dir, os.path.dirname(resultpngloc))
    
                #destination dir
                d_dir = os.path.join(presentation_dir, output_dir_name)
                if os.path.isdir( d_dir ):
                    rmtree(d_dir) # or move(presentation_dir + output_dir_name, presentation_dir + output_dir_name + '_old')
    
                log.debug('source dir is ' + str(s_dir))
                log.debug('destination dir is '+str(d_dir))
                copytree(s_dir, d_dir)
    
                if result.resulttype.overlaytype == 'ANIMATEDMAPOVERLAY':
                    stype = PresentationSource.SOURCE_TYPE_SERIE_PNG_FILES 
                else:
                    stype = PresentationSource.SOURCE_TYPE_PNG_FILE
                    
                source, new = PresentationSource.objects.get_or_create(file_location = output_file_name, type = stype)
                source.t_source = datetime.datetime.now()
                source.save()
    
                grid, new = PresentationGrid.objects.get_or_create(presentationlayer = pl, defaults={'rownr': height, 'colnr': width, 'gridsize': gridsize})
                grid.bbox_orignal_srid = 28992
                grid.png_default_legend = source
    
                #left lower
                ll = Point(south,west, srid = grid.bbox_orignal_srid )
                #right upper
                ru = Point(north,east, srid = grid.bbox_orignal_srid )
                poly = Polygon([ll,ru,ru,ll])
                poly.transform(4326)
                grid.extent = MultiPolygon(poly)
                grid.save()
                
                if result.resulttype.overlaytype == 'ANIMATEDMAPOVERLAY':
                    if not result.startnr:
                        result.startnr = result.firstnr
    
                    animation, new = Animation.objects.get_or_create( presentationlayer = pl, defaults={'firstnr': result.firstnr, 'lastnr': result.lastnr, 'startnr':result.startnr , 'delta_timestep': (1/24) } )
    
                    animation.firstnr = result.firstnr
                    animation.lastnr = result.lastnr
                    animation.startnr = result.startnr
                    log.debug("save animation with numbers %i tot %i"% (result.firstnr, result.lastnr))
                    animation.save()

        except IOError, e:
            log.error('error creating source')
            log.error(e)
            if pl_new:
                pl.delete()
            

def perform_presentation_generation(settings, scenario_id):
    """main routine

    """
    #setup the django environment 
    #from django.core.management import setup_environ
    #setup_environ(settings)   

    from lizard.flooding.models import Scenario, PresentationType
    
    scenario = Scenario.objects.get(id = scenario_id)    
    #get ids of results of this scenario
    #results_list = list(scenario.result_set.values_list('id', flat=True))
    #get all active presentation_types, made from results of flooding
    presentation_types = PresentationType.objects.filter(active=True, custom_indicator__name='flooding_result').exclude(code='damage_embankments')

    for pt in presentation_types:
        model_node, model_branch = (None, None)
        #check location types, create shapefile
        
        if pt.geo_type == PresentationType.GEO_TYPE_GRID:
            log.debug('type grid')
            successful = get_or_create_pngserie_with_defaultlegend_from_old_results(scenario, pt)
            pass
        elif pt.geo_type in [PresentationType.GEO_TYPE_POLYGON, PresentationType.GEO_TYPE_LINE, PresentationType.GEO_TYPE_POINT]:
            log.debug('type shape')
            successful = get_or_create_shape_layer(scenario, pt, False)
        elif pt.geo_type == PresentationType.GEO_TYPE_NO_GEOM:
            log.debug('type no geom')
            log.debug('this is not for this task')
            pass
        


    presentation_types = PresentationType.objects.filter(active = True, custom_indicator__name = 'flooding_geom')

    for pt in presentation_types:
        model_node, model_branch = (None, None)
        #check location types, create shapefile
        
        if pt.geo_type == PresentationType.GEO_TYPE_GRID:
            log.debug('type grid')
            log.debug('this is not for this task')
            pass
        elif pt.geo_type in [PresentationType.GEO_TYPE_POLYGON, PresentationType.GEO_TYPE_LINE, PresentationType.GEO_TYPE_POINT]:
            log.debug('type shape')
            successful = get_or_create_shape_layer(scenario, pt, True)
        elif pt.geo_type == PresentationType.GEO_TYPE_NO_GEOM:
            log.debug('type no geom')
            log.debug('this is not for this task')
            pass



    return True


if __name__ == '__main__':
    loglevel = logging.DEBUG

    logging.basicConfig(level = loglevel, format='%(asctime)s %(levelname)s %(message)s' ,)


    scenarios = Scenario.objects.filter(status_cache__in = (Scenario.STATUS_CALCULATED, Scenario.STATUS_APPROVED)).order_by('id') # filter(id = 63)
    for scenario in scenarios:
        log.info('scenario: ' + str(scenario.id))
        perform_presentation_generation(settings, scenario.id)
