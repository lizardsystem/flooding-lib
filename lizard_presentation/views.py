# -*- coding: utf-8 -*-
from zipfile import ZipFile
import StringIO
import datetime
import logging
import math
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.ticker import Formatter
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, LinearLocator
from osgeo import ogr
import PIL.Image
import mapnik
import matplotlib.pyplot as plt

from lizard_base.models import Setting
from lizard_presentation.models import Field, SupportLayers
from lizard_presentation.models import PresentationType, PresentationLayer
from lizard_presentation.models import PresentationGrid
from lizard_presentation.permission_manager import PermissionManager
from lizard_visualization.mapnik_legend import MapnikPointLegend
from lizard_visualization.models import ShapeDataLegend
from lizard_visualization.symbol_manager import SymbolManager
from nens.mock import Stream
from nens.sobek import HISFile

log = logging.getLogger('nens.web.presentation.views')



def external_file_location(filename):
    """Return full filename of file that's on smb (currently)

    Old: look in database for config value and request smb file from windows.

    New: look if django setting exists and then assume a mounted directory.

    """
    if hasattr(settings, 'EXTERNAL_PRESENTATION_MOUNTED_DIR'):
        # smb mounted on linux.
        base_dir = settings.EXTERNAL_PRESENTATION_MOUNTED_DIR
        filename = filename.replace('\\', '/')
        full_name = os.path.join(base_dir, filename)
    else:
        # Windows direct smb link.
        base_dir = Setting.objects.get( key = 'presentation_dir' ).value
        full_name = os.path.join(base_dir, filename.lstrip('\\').lstrip('/'))
    return str(full_name)


def service_get_presentationlayer_settings(
    request, pl_id):
    """get_settings of presentationlayer
    return:
        overlaytype: presentationtype_overlaytype - integer - (wms, map, general, (point, line))
        type: presentationtype_valuetype - integer - (timeserie, classification, singlevalue, static)
        has_value_source (kan ik waarden of grafieken van een punt opvragen??)
        legend: array of legends with:
                id:
                name:
                in case of default: dtype (0=personal default, 1=project default, 2=presentationType default)
    in case of grid:
        extent (in original srid) - north, south, west,east
        srid
        nrrows
        nrcols
        gridsize
    in case of animation:
        firstnr (nr first timestep)
        startnr (where default starts the animation slider)
        lastnr  (nr last timestep)
        dt (delta time between timesteps)
    in case of classification:
        firstnr (nr first class)
        startnr (default class, which is first showed when )
        lastnr  (nr last timestep)
        array of class boundaries
        voor resultaten met figuren, haalt afmetingen en extents op
    """
    pl = get_object_or_404(PresentationLayer, pk = pl_id)
    pm = PermissionManager(request.user)
    if not pm.check_permission(pl, PermissionManager.PERMISSION_PRESENTATIONLAYER_VIEW):
        raise Http404

    rec = {}
    if pl.presentationtype.geo_type == PresentationType.GEO_TYPE_GRID:
        try:
            pl.presentationgrid
        except PresentationGrid.DoesNotExist:
            return HttpResponse(simplejson.dumps({}), mimetype="application/json")

        rec['bounds'] = {}
        rec['bounds']['projection'] = pl.presentationgrid.bbox_orignal_srid

        if pl.presentationgrid.bbox_orignal_srid == 28992:
            rec['bounds']['south'], rec['bounds']['west'], rec['bounds']['north'], rec['bounds']['east']  = pl.presentationgrid.extent.extent
            rec['bounds']['projection'] = 28992
        else:
            rec['bounds']['west'], rec['bounds']['south'], rec['bounds']['east'], rec['bounds']['north'] = pl.presentationgrid.extent.extent
            rec['bounds']['projection'] = 4326

        rec['height'] = pl.presentationgrid.rownr
        rec['width'] = pl.presentationgrid.colnr
        rec['gridsize'] = pl.presentationgrid.gridsize

    anim = {}
    # Added False at the end of the line to be sure for testing that it will never execute the code and False
    if pl.presentationtype.value_type == PresentationType.VALUE_TYPE_TIME_SERIE:
        anim['firstnr'] = pl.animation.firstnr
        anim['lastnr'] = pl.animation.lastnr
        anim['options'] = {}
        anim['options']['startnr'] = pl.animation.startnr
        if (pl.animation.delta_timestep > 0):
            anim['options']['delta'] = pl.animation.delta_timestep * 24 * 3600

    #legends = ShapeDataLegend.objects.filter(presentationtype = pl.presentationtype)
    legends = pm.get_legends(pl)

    #legendObjects = [(l.id, l.name) for l in legends]
    legend_objects = [{'id': l.id, 'name': l.name} for l in legends]

    default_legend = ShapeDataLegend.objects.get(pk = pl.presentationtype.default_legend_id)

    log.debug( 'got default legend' )

    info = {}
    info['rec'] = rec
    info['anim'] = anim
    info['legends'] = legend_objects
    info['default_legend'] = {'id': default_legend.id, 'name': default_legend.name}

    if pl.presentationtype.value_type == PresentationType.VALUE_TYPE_TIME_SERIE and pl.presentationtype.geo_type in [PresentationType.GEO_TYPE_POLYGON, PresentationType.GEO_TYPE_LINE, PresentationType.GEO_TYPE_POINT]:
        #WMS service, start caching results for later requests
        #service_get_wms_of_shape(request,  2,  2, (-1,-1,0,0,), pl_id, default_legend.id,  0 )

        anim['lastnr'] = pl.animation.lastnr
        pass

    log.debug( 'json dump van info' )
    log.debug( simplejson.dumps(info) )
    return HttpResponse(simplejson.dumps(info), mimetype="application/json")


def service_get_wms_of_shape(
    request, width, height, bbox, presentationlayer_id, legend_id, timestep ):
    """
    width = int
    height = int
    bbox = tuple
    """
    pl = get_object_or_404(PresentationLayer, pk=presentationlayer_id)
    if legend_id == -1:
        legend_id = pl.presentationtype.default_legend_id

    #presentation_dir = Setting.objects.get( key = 'presentation_dir' ).value

    #################### set up map ###################################
    log.debug( 'start setting up map ' + str(datetime.datetime.now()))

    m = mapnik.Map(width, height)
    spherical_mercator = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over'

    m.srs = spherical_mercator
    m.background = mapnik.Color('transparent')
    #p = mapnik.Projection(spherical_mercator)

    log.debug('start setting up legend ' + str(datetime.datetime.now()))
    #################### set up legend ###################################

    mpl = cache.get('legend_' + str(legend_id))
    if mpl == None:
        sdl = get_object_or_404(ShapeDataLegend, pk=legend_id)
        if pl.presentationtype.geo_type in [PresentationType.GEO_TYPE_POLYGON, PresentationType.GEO_TYPE_LINE, PresentationType.GEO_TYPE_POINT]:
            sm = SymbolManager('media/lizard_presentation/symbols/')
            mpl = MapnikPointLegend(sdl, sm)
            cache.set('legend_' + str(legend_id), mpl , 300)


    mapnik_style = mpl.get_style() #get mapnik style with a set of rules.
    fields = mpl.get_presentationtype_fields()
    m.append_style('1', mapnik_style)

    log.debug( 'start setting up lijntje ' + str(datetime.datetime.now()) )
    #################### supportive layers ###################################
    if SupportLayers.objects.filter(presentationtype = pl.presentationtype ).count() > 0:
        supportive_layers = pl.presentationtype.supported_presentationtype.supportive_presentationtype.all()

        sl = mapnik.Style()
        rule_l = mapnik.Rule()

        rule_stk = mapnik.Stroke()
        rule_stk.color = mapnik.Color(3,158,137)
        rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
        rule_stk.width = 2.0
        rule_l.symbols.append(mapnik.LineSymbolizer(rule_stk))
        sl.rules.append(rule_l)
        m.append_style('Line Style', sl)

        for spt in supportive_layers:
            log.debug( 'supportive layer with id: ' + str(spt.id) )


            #warning! works only for flooding scenarios
            if pl.scenario_set.count() > 0:
                scenario = pl.scenario_set.get()
                layers = PresentationLayer.objects.filter(presentationtype = spt, scenario = scenario)

                if len(layers)>0:
                    log.debug( 'supportive layer found for this presentationlayer' )
                    layer = layers[0]

                    lyrl = mapnik.Layer('lines', spherical_mercator)
                    lyrl.datasource = mapnik.Shapefile(file=external_file_location(layer.presentationshape.geo_source.file_location))

                    lyrl.styles.append('Line Style')
                    m.layers.append(lyrl)


    #for geo_source in geo_sources:
    #    lyrl.datasource = mapnik.Shapefile(file=str(presentation_dir + '\\' + geo_source.file_location))
    #    lyrl.srs = '+proj=tmerc +lat_0=0 +lon_0=84 +k=0.999900 +x_0=500000 +y_0=0 +a=6377276.345 +b=6356075.413140239 +units=m +no_defs'
    #'+proj=utm +zone=45 +a=6377276.345 +b=6356075.413140239 +units=m +no_defs'
    #    lyrl.styles.append('Line Style')
    #    m.layers.append(lyrl)

    #################### read data ###################################
    #read source and attach values
    lyr = mapnik.Layer('points',spherical_mercator)
    lyr.datasource = mapnik.PointDatasource()
    log.debug(  'ready setting up map ' + str(datetime.datetime.now()) )
    log.debug(  'start reading point cache ' + str(datetime.datetime.now()) )
    points = cache.get('model_nodes_' + str(presentationlayer_id) + '_' + str(timestep) +'_' + str(legend_id))
    log.debug( 'ready reading point cache ' + str(datetime.datetime.now()) )


    if points == None:
        log.debug(  'start reading points from shape and his file ' + str(datetime.datetime.now()) )
        points = []

        drv = ogr.GetDriverByName('ESRI Shapefile')
        shapefile_name = external_file_location(pl.presentationshape.geo_source.file_location)
        ds = drv.Open(shapefile_name)
        layer = ds.GetLayer()

        has_his_file_field = False
        has_geo_file_field = False
        geo_fields = []
        log.debug( 'fields are: ' + str(fields))
        for nr in fields:
            field = fields[nr]
            if field.source_type == Field.SOURCE_TYPE_VALUE_SOURCE_PARAM:
                has_his_file_field = True
                his_field = field
                #only his files yet supported. read needed data
                log.debug( 'start reading hiscache' + str(datetime.datetime.now()) )
                his = cache.get('his_' + str(presentationlayer_id) )
                log.debug( 'ready reading hiscache' + str(datetime.datetime.now()) )

                if his == None:
                    log.debug( 'read hisfile' + str(datetime.datetime.now()) )
                    zip_name = external_file_location(pl.presentationshape.value_source.file_location)
                    input_file = ZipFile(zip_name, "r")
                    if pl.presentationtype.geo_source_filter:
                        filename = pl.presentationtype.geo_source_filter
                    else:
                        filename = input_file.filelist[0].filename

                    his = HISFile(Stream(input_file.read(filename)))
                    input_file.close()
                    log.debug( 'ready reading hisfile' + str(datetime.datetime.now()))
                    cache.set('his_' + str(presentationlayer_id) , his , 3000)

                values = his.get_values_timestep_by_index(his.get_parameter_index(his_field.name_in_source), timestep)

            elif field.source_type == Field.SOURCE_TYPE_GEO_SOURCE_COL:
                has_geo_file_field = True
                geo_fields.append(field)
            else:
                log.debug(  'field source type ' + field.source_type + ' not yet supported' )

        if (layer.GetFeatureCount()>0):
            feature = layer.next()
            id_index = feature.GetFieldIndex('id')

            for field in geo_fields:
                field.index_nr = feature.GetFieldIndex(str(field.name_in_source))

            layer.ResetReading()
        ############################# place features in the right 'legend box'


        for feature in layer:
            point = feature.geometry()

            input_dict = {}

            if has_his_file_field:
                #get id form geosource, needed for reading hisfile
                id = pl.presentationtype.value_source_id_prefix + str(feature.GetField(id_index).strip())
                if pl.presentationtype.absolute:
                    try:
                        input_dict[his_field.name_in_source] = abs(values.get(id, None))
                        if values.get(id, None) > 1:
                            pass

                    except TypeError:
                        input_dict[his_field.name_in_source] = None
                else:
                    input_dict[his_field.name_in_source] = values.get(id, None)

            if has_geo_file_field:
                for field in geo_fields:
                    input_dict[field.name_in_source] = feature.GetField(field.index_nr)

            rule_name = mpl.get_rule_name(input_dict)

            if pl.presentationtype.geo_type == 3:
                x = (point.GetX(0) + point.GetX(1))/2
                y = (point.GetY(0) + point.GetY(1))/2
            else:
                x = point.GetX()
                y = point.GetY()

            #rule_name = str('1_neerslag_64_0010000100_24x24_0_0')
            points.append((x, y, "NAME", rule_name))
       # Clean up
        ds.Destroy()
        log.debug( 'ready reading points form shape en his file ' + str(datetime.datetime.now()) )

        cache.set('model_nodes_' + str(presentationlayer_id) + '_' + str(timestep) + '_' + str(legend_id), points , 300)

    log.debug(  'start making memory datasource ' + str(datetime.datetime.now()) )
    for x,y,name,rule_name in points:
        lyr.datasource.add_point(x,y,name,rule_name)

    log.debug(  'finish making memory datasource ' + str(datetime.datetime.now()) )

    lyr.styles.append('1')
    m.layers.append(lyr)

    if presentationlayer_id in [62007, 62008]:
        m = mapnik.Map(width, height)
        spherical_mercator = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

        m.srs = spherical_mercator
        m.background = mapnik.Color('transparent')

        sl = mapnik.Style()
        rule_l = mapnik.Rule()

        rule_stk = mapnik.Stroke()
        rule_stk.color = mapnik.Color(3,158,137)
        rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
        rule_stk.width = 2.0
        rule_l.symbols.append(mapnik.LineSymbolizer(rule_stk))
        sl.rules.append(rule_l)
        m.append_style('Line Style2',sl)

        scenario = pl.scenario_set.get()
        layers = PresentationLayer.objects.filter(presentationtype = spt, scenario = scenario)
        log.debug( 'supportive layer found for this presentationlayer' )

        rds = mapnik.Projection("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs")
        lyrl = mapnik.Layer('lines', rds)
        lyrl.datasource = mapnik.Shapefile(file=external_file_location(str(presentation_dir + '\\' + pl.presentationshape.geo_source.file_location)))
        lyrl.styles.append('Line Style2')
        m.layers.append(lyrl)

    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox)) #lyrl.envelope

    log.debug(  'start render map ' + str(datetime.datetime.now()) )
    img = mapnik.Image(width,height)
    mapnik.render(m,img)
    log.debug(  'ready render map ' + str(datetime.datetime.now()) )

    log.debug( 'start PIL ' + str(datetime.datetime.now()) )
    # you can use this if you want te modify image with PIL
    imgPIL = PIL.Image.fromstring('RGBA', (width,height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')#,transparency = 10
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    log.debug(  'end PIL ' + str(datetime.datetime.now()) )
    response['Content-type'] = 'image/png'
    log.debug(  'ready sending map ' + str(datetime.datetime.now()) )
    return response



def service_get_gridframe(request, presentationlayer_id, legend_id, framenr=0):
    """get png of grid of given timestep, with given legend (of legend is None, use default legend)
    input
        presentationlayer
        legend
        timestep

    Conditions:
    - from given scenario (check permission for given scenario)

    output:
        png
    """
    pl = get_object_or_404(PresentationLayer, pk=presentationlayer_id)

    log.debug('get png name')
    png_name = external_file_location(pl.presentationgrid.png_default_legend.file_location)
    if pl.presentationtype.value_type == 3:
        log.debug('get png name with number.')
        numberstring = '%04i' % framenr
        png_name = png_name.replace('####',numberstring)

    log.debug('load files %s'%png_name)

    response = HttpResponse(open(png_name,'rb').read())
    response['Content-type'] = 'image/png'
    return response

def service_get_shapes(
    request,  x,y, presentationlayer_id ,precision = 100):
    """ get shapes near point (mouseclick)
    input:
        x, y (coordinates of point in googlemercator 900913)
        precision (give all points in a square of 'precision' around point)
        presentationlayer
    output:
        array of shapes with:
        id shape
        name shape
    """
    pl = get_object_or_404(PresentationLayer, pk=presentationlayer_id)
    #presentation_dir = Setting.objects.get( key = 'presentation_dir' ).value
    shapefile_name = external_file_location(pl.presentationshape.geo_source.file_location)

    drv = ogr.GetDriverByName('ESRI Shapefile')
    ds = drv.Open(shapefile_name)
    layer = layer = ds.GetLayer()
    layer.SetSpatialFilterRect(x-precision, y-precision,x+precision,y+precision)

    if (layer.GetFeatureCount()>0):
        feature = layer.next()
        id_index = feature.GetFieldIndex('id')
        layer.ResetReading()

    answer=[{"id":feature.GetField(id_index),"name":feature.GetField(id_index)} for feature in layer]

    return HttpResponse(simplejson.dumps(answer), mimetype='application/json')


class TimestepFormatter(Formatter):
    def __call__(self, x, pos=None):
        log.debug( 'timestep format: ' + str(math.floor(x/24)) )
        return "Dag %d: %u uur" % (math.floor(x/24), x%24)

def service_get_graph_of_shape(request, width, height, sobek_ids, presentationlayer_id):
    """
        - This service returns a PNG image with the given width and height
        - The PNG contains a graph of the results belonging to the result_id and sobek_ids
    input:
        widht and height of returning image
        array of shape_ids which will be shown
        presentationlayer_id

    return:
        png
    """
    # Opmerking Bastiaan: caching van his-object geeft weinig tijdwinst

    pl = get_object_or_404(PresentationLayer, pk=presentationlayer_id)

    #Get information from request
    graph_width = float(request.GET['graphwidth'])
    graph_height = float(request.GET['graphheight'])

    #Set dpi
    graph_dpi = 55

    #Create figure and subplot to draw on
    fig = plt.figure(facecolor='white', edgecolor='white', figsize=(graph_width/graph_dpi, graph_height/graph_dpi), dpi=graph_dpi)

    #Add axes 'manually' (not via add_subplot(111) to have control over the position
    #This is necessary as we use long labels
    ax_left = 0.11
    ax_bottom  = 0.21
    ax=fig.add_axes([ax_left, ax_bottom, 0.95-ax_left, 0.95-ax_bottom])

    #Read Sobek data and plot it
    plots=dict() # dictionary necessary for creating the legend at the end of this method
    for sobek_id in sobek_ids:
        #limit id to 20 characters, because hisfiles has max 20 characters . this can refer to the wrong location
        time_steps, values = read_his_file(sobek_id[:20], pl)
        plot =  ax.plot(time_steps, values, '-', linewidth = 3)
        plots['Sobek_id='+str(sobek_id)]=plot

    #Create locators
    [min_locator, maj_locator] = get_time_step_locators(len(time_steps),(time_steps[1] -time_steps[0])  )

    #Set formatting of the x-axis and y-axis
    ax.xaxis.set_major_formatter(TimestepFormatter())
    ax.xaxis.set_major_locator(maj_locator)
    ax.xaxis.set_minor_locator(min_locator)
    fig.autofmt_xdate()

    ax.yaxis.set_major_locator(LinearLocator())
    ax.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))

    ax.grid(True, which='major')
    ax.grid(True, which='minor')

    #Set labels
    plt.xlabel("Tijdstip")
    plt.ylabel(pl.presentationtype.unit)
    ax.set_title(pl.presentationtype.name)

    #Set legend
    ax.legend((v for k,v in plots.iteritems()), (k for k,v in plots.iteritems()), 'upper left', shadow=True)

    #Return figure as png-file
    log.debug(  'start making picture' + str(datetime.datetime.now()) )
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    log.debug( 'ready making picture' + str(datetime.datetime.now()) )
    return response

def get_time_step_locators(num_time_steps, dt):
    """
    - Create locators for the major ticks and minor ticks, based on the number
      of time_steps
    - Returns [min_locator, maj_locator]
    """

    if 0 <= num_time_steps <= 32:
        maj_locator= MultipleLocator(4*dt)
        min_locator= MultipleLocator(4*dt)
    elif 32 < num_time_steps <=64:
        maj_locator= MultipleLocator(8*dt)
        min_locator= MultipleLocator(4*dt)
    elif 64 < num_time_steps <= 96:
        maj_locator= MultipleLocator(12*dt)
        min_locator= MultipleLocator(4*dt)
    elif 96 < num_time_steps:
        maj_interval = math.ceil(dt*num_time_steps/8)       #values_timespan.days
        maj_locator = MultipleLocator(maj_interval +1)
        min_locator = MultipleLocator(math.ceil(maj_interval/2))
    return [min_locator, maj_locator]

def service_get_graph_grid(request, width, height, shape_ids, presentationlayer_id):
    """
        - This service returns a PNG image with the given width and height
        - The PNG contains a graph of the results belonging to the result_id and sobek_ids
    input:
        widht and height of returning image
        array of shape_ids which will be shown
        presentationlayer_id

    return:
        png
    """
    pass

def service_get_general_values(request, scenario_id, filter_type):
    """ return table with name and value of  presentationlayers of type 'general'
    input:
        scenario
        filter_type = custom_filter_type (defined for each presentationtype)
    return:
        png
    """
    pass


def timedelta_to_float(td):
    """Converts a timedelta object to float representation. If it fails, return None"""
    try:
        return float(td.days) + float(td.seconds)/float(86400)
    except:
        return None


def read_his_file(sobek_id, presentationlayer):
    """
    - Return [time_steps, values] read in the his-file and belonging to the sobek_id and result_id
    """

    pl = presentationlayer

    his = cache.get('his_' + str(presentationlayer.id) )
    if his == None:
        #presentation_dir = Setting.objects.get( key = 'presentation_dir' ).value
        zip_name = external_file_location(pl.presentationshape.value_source.file_location)

        input_file = ZipFile(zip_name, "r")

        if presentationlayer.presentationtype.geo_source_filter:
            filename = pl.presentationtype.geo_source_filter
        else:
            filename = input_file.filelist[0].filename

        his = HISFile(Stream(input_file.read(external_file_location(filename))))
        input_file.close()
        cache.set('his_' + str(presentationlayer.id) , his , 30)

    sobek_id = presentationlayer.presentationtype.value_source_id_prefix + sobek_id
    #else:
    #    sobek_id = 'p_' + sobek_id

    field = presentationlayer.presentationtype.field_set.get(source_type = Field.SOURCE_TYPE_VALUE_SOURCE_PARAM)
    timeserie = his.get_timeseries( sobek_id, field.name_in_source, None, None, list )
    t0 = timeserie[0][0]
    time_steps  = [timedelta_to_float(t-t0)*24 for (t,v) in timeserie]
    if presentationlayer.presentationtype.absolute:
        values = [abs(v) for (t,v) in timeserie]
    else:
        values = [v for (t,v) in timeserie]


    #Return data
    return [time_steps, values]

@login_required
def overview_permissions(request):
    """
    Gives an overview of all permissions
    """
    if not(request.user.is_staff):
        raise Http404


    request_username = request.GET.get('user', None)
    if request_username is None:
        request_user = request.user
    else:
        request_user = User.objects.get(username=request_username)

    request_presentationlayer_id = request.GET.get('presentationlayer_id', None)
    if request_presentationlayer_id is None:
        request_presentationlayer = None
        text = 'Wat mag user "%s" uberhaupt voor dingen doen?'%request_user
        source_application_choices = PresentationLayer.SOURCE_APPLICATION_CHOICES
    else:
        request_presentationlayer = PresentationLayer.objects.get(
            pk=int(request_presentationlayer_id))
        text = 'Wat mag user "%s" dingen doen voor presentationlayer "%s".'%(request_user, str(request_presentationlayer))
        source_application_choices = ((request_presentationlayer.source_application, PresentationLayer.SOURCE_APPLICATION_DICT[request_presentationlayer.source_application]),)

    header = range(1, 11)
    permission_list = []
    pm = PermissionManager(request_user)

    for app_code, app_name in source_application_choices:
        app_block = {}
        app_block['title'] = app_name
        app_block['header'] = header
        app_block['table'] = []
        for permission in [PermissionManager.PERMISSION_PRESENTATIONLAYER_VIEW,
                           PermissionManager.PERMISSION_PRESENTATIONLAYER_EDIT]:
            row = [PermissionManager.PERMISSION_DICT[permission]]
            for permission_level in header:
                row.append(pm.check_permission_app(app_code, permission_level, permission, presentationlayer=request_presentationlayer))
            app_block['table'].append(row)
        permission_list.append(app_block)

    return render_to_response('presentation/overview_permissions.html',
                              {'permissions': permission_list,
                               'user': request.user,
                               'text': text,
                               })
@never_cache
def uber_service(request):
    """Collection of all available services.

    This function calls the actual functions
    """
    q = request.GET
    action = q.get('action',q.get('ACTION') ).lower() #makes it lower case
    #action_cap = q.get('ACTION').lower()

    if action == 'get_presentationlayer_settings':
        pl_id = q.get('result_id', None)
        return service_get_presentationlayer_settings(request,
                                               pl_id=pl_id)
    elif action == 'get_gridframe':
        presentationlayer_id = q.get('result_id', None)
        legend_id = q.get('legend_id', None)
        framenr = q.get('framenr', 0)
        return service_get_gridframe(request,
                                        presentationlayer_id=presentationlayer_id,
                                        legend_id = legend_id,
                                        framenr = int(framenr))

    elif action == 'get_shapes':
        presentationlayer_id = q.get('result_id', None)
        x =  q.get('x', None)
        y =  q.get('y', None)
        precision =  q.get('precision', 50)
        return service_get_shapes(request,
                                 x=float(x),
                                 y=float(y),
                                 presentationlayer_id=presentationlayer_id,
                                 precision = float(precision))

    elif action == 'get_graph_of_shape':
        presentationlayer_id = q.get('result_id', None)
        graphwidth =  q.get('graphwidth', None)
        graphheight =  q.get('graphheight', None)
        sobek_ids_string =  q.get('sobek_id', None)
        sobek_ids = sobek_ids_string.split(',')
        return service_get_graph_of_shape(request,
                                      width= int(graphwidth),
                                      height= int(graphheight),
                                      sobek_ids = sobek_ids,
                                      presentationlayer_id=presentationlayer_id)

    elif action == 'get_wms_of_shape':
        presentationlayer_id = q.get('RESULT_ID', None)
        bbox =  q.get('BBOX', None)
        width =  q.get('WIDTH', None)
        height =  q.get('HEIGHT', None)
        legend_id =  q.get('LEGEND_ID', -1)
        timestep =  q.get('TIMESTEP', 6)
        return service_get_wms_of_shape(request,
                                      width= int(width),
                                      height= int(height),
                                      bbox= tuple([float(value) for value in bbox.split(',')]),
                                      presentationlayer_id=presentationlayer_id,
                                      legend_id = int(legend_id),
                                      timestep = int(timestep))

    # elif action == 'get_wms_of_shape_nepal':
    #     from views_dev import service_get_wms_of_shape_nepal
    #     presentationlayer_id = q.get('RESULT_ID', None)
    #     bbox =  q.get('BBOX', None)
    #     width =  q.get('WIDTH', None)
    #     height =  q.get('HEIGHT', None)
    #     legend_id =  q.get('LEGEND_ID', 1)
    #     timestep =  q.get('TIMESTEP', 6)
    #     return  service_get_wms_of_shape_nepal(request,
    #                                   width= int(width),
    #                                   height= int(height),
    #                                   bbox= tuple([float(value) for value in bbox.split(',')]),
    #                                   presentationlayer_id=presentationlayer_id,
    #                                   legend_id = int(legend_id),
    #                                   timestep = int(timestep))
