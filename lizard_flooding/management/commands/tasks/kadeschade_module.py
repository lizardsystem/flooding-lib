#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#*   
#***********************************************************************
#*                      All rights reserved                           **
#*   
#*   
#*                                                                    **
#*  #*   
#*   
#***********************************************************************
#* Library    : Channel embankement damage module
#* Purpose    : 
#* Function   : calc_damage(scenario_id)
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

import sys
if sys.version_info < (2, 4):
    print "I think I need version python2.4 and I was called from %d.%d" % sys.version_info[:2]

import logging

log = logging.getLogger('nens.lizard.kadebreuk.embankment.dammage') 

if __name__ == '__main__':
    sys.path.append('..')
    
    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)
          
  
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

from zipfile import ZipFile, ZIP_DEFLATED
import StringIO
from nens.sobek import HISFile
from osgeo import ogr, osr
import os
import datetime

def calc_damage(scenario_id):
    log.debug('read django and lizard settings')
    source_dir = Setting.objects.get( key = 'source_dir' ).value
    result_dir = Setting.objects.get( key = 'destination_dir' ).value
    presentation_dir = Setting.objects.get( key = 'presentation_dir' ).value
    
    log.debug('read scenario and file settings')
    dest_shape = os.path.join('flooding', 'scenario', str(scenario_id), 'embank_damage.shp')

    scenario = Scenario.objects.get(pk=scenario_id)
    pt = PresentationType.objects.get(code = 'damage_embankments')
    
    try:
        #damage settings
        extwater_models = SobekModel.objects.filter(scenariobreach__scenario=scenario, embankment_damage_shape__isnull=False)
        if extwater_models.count() == 0:
            log.info('no externalwatermodel or embankment_damage_shape for this scenario. Scenario skipped')
            return True, 'skipped 1 '
        else:
            model = extwater_models[0]
            
        
        result_waterlevel = Result.objects.filter(scenario = scenario, resulttype=13)

        if result_waterlevel.count() >0:
            his_zip_name = os.path.join(result_dir, result_waterlevel[0].resultloc)
        else:
            log.warning('Not enough results for calculation of embankment damage. Scenario skipped')
            return True, 'skipped 2 '

    except Result.DoesNotExist, e:
        log.warning('Not enough results for calculation of embankment damage. Scenario skipped')
        return True, 'skipped 3 '
    
    shapefile_name = os.path.join(source_dir, model.embankment_damage_shape)


    log.debug('read damage settings')
    damage ={'onvhard':500,#for each m
             'verhard':1000,#for each m
             'huizen':3000,#for each m2
             'woonboot':50000}#each
    
    start_damage ={'zonder verdediging':0.5,
             'met beschoeiing':0.5,
             'stalen damwand':0.5,
             'stortsteen':0.5,
             'woonboot':1.0,
             'kleidijk':3.0,
             'veendijk':2.5,
             'zanddijk':2.0,
             'Klei':3.0,
             'Veen':2.5,
             'Zand':2.0,                   
             None:0.5}
    
    full_damage ={'zonder verdediging':1.0,
             'met beschoeiing':1.0,
             'stalen damwand':1.0,
             'stortsteen':2.0,
             'woonboot':1.0,
             'kleidijk':3.0,
             'veendijk':2.5,
             'zanddijk':2.0,
             'Klei':3.0,
             'Veen':2.5,
             'Zand':2.0,                    
             None:1.0}
    
    
    log.debug('open source shapefile')
    drv = ogr.GetDriverByName('ESRI Shapefile')
    source = drv.Open(str(shapefile_name))
    source_layer = source.GetLayer()
    
    log.debug('create dest shapefile')
    output_dir = os.path.dirname(os.path.join(presentation_dir, dest_shape))
    if not os.path.isdir(output_dir):
        log.debug('create output dir' + output_dir)
        os.makedirs(output_dir)

    dest_shape_full = os.path.join(presentation_dir, dest_shape)
    if os.path.isfile(dest_shape_full):
        log.debug('shapefile already exist, delete shapefile.' )
        os.remove(dest_shape_full)
        os.remove(dest_shape_full.replace('.shp','.shx'))
        os.remove(dest_shape_full.replace('.shp','.dbf'))
        os.remove(dest_shape_full.replace('.shp','.prj'))  

    print 
    dest = drv.CreateDataSource( str(dest_shape_full) )
    dest_srs = osr.SpatialReference()
    dest_srs.ImportFromProj4('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')        
    dest_layer = dest.CreateLayer(dest.GetName(), geom_type = ogr.wkbLineString, srs = dest_srs)
    
    log.debug('create geo-transformation')
    #source_srs = source_layer.GetSpatialRef()
    #transformation = ogr.osr.CoordinateTransformation(source_srs,dest_srs)
    
    log.debug('get field ids')
    if (source_layer.GetFeatureCount()>0):
        feature = source_layer.next()
        id_index = feature.GetFieldIndex('ID_1')
        length_index = feature.GetFieldIndex('LENGTE')
        onverhard_index = feature.GetFieldIndex('ONVERH')
        verhard_index = feature.GetFieldIndex('VERHARD')
        huizen_index = feature.GetFieldIndex('HUIZEN')
        woonboot_index = feature.GetFieldIndex('WOONBOOT')
        kade_type_index = feature.GetFieldIndex('BSOORT') 
        source_layer.ResetReading()
    
    log.debug("create 'source' fields in new shapefile")
    dest_layer.CreateField(ogr.FieldDefn('id', ogr.OFTString))
    dest_layer.CreateField(ogr.FieldDefn('length', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('onverh', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('verhard', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('huizen', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('woonboot', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('kade_type', ogr.OFTString))
        
    log.debug("create 'result' fields in new shapefile")
    dest_layer.CreateField(ogr.FieldDefn('daling', ogr.OFTReal))
    dest_layer.CreateField(ogr.FieldDefn('perc_bezw', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_kade', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_bebouw', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_woonboot', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_totaal', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_max', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_perc', ogr.OFTInteger))
    dest_layer.CreateField(ogr.FieldDefn('sch_per_m', ogr.OFTReal))
    
    #openen hisfile
    log.debug( 'read hisfile' )
    
    input_file = ZipFile(his_zip_name, "r")
    for filename in input_file.namelist():
        if filename.lower()=='calcpnt.his':
            his = HISFile(StringIO.StringIO(input_file.read(filename)))
            break
    
    
    input_file.close()
    
    def get_perc_bezw(daling, start_damage, full_damage):
        if daling <= start_damage:
            return 0.0
        elif daling >= full_damage:
            return 100.0
        else:
            return 100*( daling - start_damage) / (full_damage - start_damage)  
    
    sum_damage = 0
    for layer in source_layer:
        #opzetten feature
        feat = ogr.Feature(feature_def=dest_layer.GetLayerDefn())
        feat.SetFID(layer.GetFID())
        
        #omzetten geometry
        geom = layer.geometry()
        #geom.TransformTo(dest_srs)
        feat.SetGeometry(geom)
        
        #omzetten basisgegevens                 
        feat.SetField('id', layer.GetField(id_index))
        feat.SetField('length', layer.GetField(length_index))
        feat.SetField('onverh', layer.GetField(onverhard_index))
        feat.SetField('verhard', layer.GetField(verhard_index))
        feat.SetField('huizen', layer.GetField(huizen_index))
        feat.SetField('woonboot', layer.GetField(woonboot_index))
        feat.SetField('kade_type', layer.GetField(kade_type_index))   
        #uitlezen peildaling uit hisfile
        try:
            daling = his.get_timeseries('c_' + layer.GetField(id_index), 'Waterlevel', None, None, list)[0][1] - min([value for date, value in his.get_timeseries('c_' + layer.GetField(id_index), 'Waterlevel', None, None, list)])
        except KeyError:
            log.debug('no value for %s'%layer.GetField(id_index))
            daling = 0.

        feat.SetField('daling', float(daling))   
        #uitvoeren berekeningen 
        type_besch = layer.GetField(kade_type_index)
        
        perc_bezw = get_perc_bezw(daling,start_damage[type_besch],full_damage[type_besch])
        feat.SetField('perc_bezw', int(perc_bezw))
        
        max_sch_kade = layer.GetField(onverhard_index) * damage['onvhard'] + layer.GetField(verhard_index)*damage['verhard']
        feat.SetField('sch_kade', int(max_sch_kade*perc_bezw/100))
        
        max_sch_bebouwing = layer.GetField(huizen_index) * damage['huizen']
        feat.SetField('sch_bebouw', int(max_sch_bebouwing*perc_bezw/100))
        
        max_sch_woonboot = layer.GetField(woonboot_index) * damage['woonboot']
        sch_woonboot = max_sch_woonboot * get_perc_bezw(daling,start_damage['woonboot'],full_damage['woonboot'])/100
        feat.SetField('sch_woonboot', int(sch_woonboot))

        sch_totaal = sch_woonboot + (max_sch_bebouwing + max_sch_kade) * perc_bezw/100
        feat.SetField('sch_totaal', int(sch_totaal))
        sum_damage += sch_totaal
        
        max_schade = max_sch_woonboot + max_sch_bebouwing + max_sch_kade
        feat.SetField('sch_max', int(max_schade))

        if max_schade > 0:
            sch_perc = 100*sch_totaal/max_schade
        else:
            sch_perc = -1
        feat.SetField('sch_perc', int(sch_perc))

        length = layer.GetField(length_index)
        if  length > 0:
            sch_per_m = sch_totaal/length
        else:
            sch_per_m = -1
        feat.SetField('sch_per_m', int(sch_per_m))   
        
        #wegschrijven
        dest_layer.CreateFeature(feat) 
    
    dest_layer.SyncToDisk()
    # Clean up
    dest.Destroy()
    source.Destroy()

    pl, pl_new= PresentationLayer.objects.get_or_create(presentationtype = pt, scenario_presentationlayer__scenario = scenario, defaults = {"value": sum_damage} )
    if pl_new:
        Scenario_PresentationLayer.objects.create(scenario = scenario, presentationlayer = pl)
    else:
        pl.value = sum_damage
        pl.save()
    
    link_type, _ = SourceLinkType.objects.get_or_create(name='flooding_scenario_embankment_damage')
    source_link, new = SourceLink.objects.get_or_create(link_id = str(scenario.id), sourcelinktype = link_type, type= 'fl_emb_dam_' + str(scenario.id)  )
    source, new = source_link.presentationsource.get_or_create(type = PresentationSource.SOURCE_TYPE_SHAPEFILE)

    source.file_location = dest_shape
    source.t_original = datetime.datetime.fromtimestamp(os.stat(str(his_zip_name))[8])
    source.t_source = datetime.datetime.now()
    source.save()

    ps, ps_new = PresentationShape.objects.get_or_create(presentationlayer = pl)
    ps.geo_source = source
    ps.save()

    return True, "ok "

    

#calc_damage(1)
