#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Bastiaan Roos
#
#******************************************************************************

from datetime import datetime
from os.path import join

from lizard_flooding.models import  EmbankmentUnit, Region
    
from django.core.management.base import BaseCommand


def load_shapefile(shapefile_name, id_field, type_field, height_field, region_field=None, source_epsg=4326):           
    
    from osgeo import ogr  #, osr
    from django.contrib.gis.geos import GEOSGeometry, LineString

     #original SRS
    oSRS=ogr.osr.SpatialReference()
    if source_epsg == 28992:
        #epsg28992 projection was defined incorrect in proj4, so define manually
        oSRS.ImportFromProj4("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs" )
    else:
        oSRS.ImportFromEPSG(source_epsg)

    #target SRS
    tSRS=ogr.osr.SpatialReference()
    tSRS.ImportFromEPSG(4326)
    poCT=ogr.osr.CoordinateTransformation(oSRS,tSRS)

    drv = ogr.GetDriverByName('ESRI Shapefile')
    source = drv.Open(str(shapefile_name))
    lyr = source.GetLayer()

        
    feature = lyr.next()
    ident_index = feature.GetFieldIndex(id_field)
    #name_field = feature.GetFieldIndex(name_field)
    height_index = feature.GetFieldIndex(height_field)
    if region_field:
        region_index = feature.GetFieldIndex(region_field)
    lyr.ResetReading()
    
    for feature in lyr:
        geom = feature.GetGeometryRef()
        geom.Transform(poCT)
        geom.FlattenTo2D()
        geometry = GEOSGeometry(geom.ExportToWkt(), srid=4326)
        print geometry.geom_type
        #if geometry.geom_type == 'LineString':
        #    print '------'
        #    geometry = LineString(geometry)
        
        
        unit_id = feature.GetField(ident_index)
        #name = feature.GetField(name_index) if feature.GetField(ident_index) is not None else 'no_name' 
        original_height = feature.GetField(height_index)
        print original_height
        
        if region_field:
            region_id = feature.GetField(region_index)
            regions = Region.objects.filter(id=region_id)
        else:
            regions = Region.objects.filter(geom__intersects=geometry)
                        
        
        for region in regions:        
            embankment_unit = EmbankmentUnit(unit_id=unit_id,
                                     type=EmbankmentUnit.TYPE_EXISTING,
                                     original_height=original_height,
                                     region=region,                   
                                     geometry=geometry)
            embankment_unit.save()
        
        
    
    return HttpResponse("Gelukt")





class Command(BaseCommand):
    args = "<filelocation >"
    help = "Load shapefile with geometries and names into EmbankmentUnits table."

    def handle(self, *args, **options):
        shapefile_name = str(args[0])
        id_field = str(args[1])
        #name_field = str(args[1])
        type_field = str(args[2])
        height_field = str(args[3])
        region_field = str(args[4])
        source_epsg = int(args[5])
        load_shapefile(shapefile_name, id_field, type_field, height_field, region_field, source_epsg)






