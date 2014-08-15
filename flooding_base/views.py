"""Views for LizardBase
author: ir. k.k.ha
see the documentation on TWiki
"""

import csv
import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core import serializers
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.utils import translation
import iso8601
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure

from flooding_base.models import Configuration
from flooding_base.models import GroupConfigurationPermission
from flooding_base.models import SubApplication
from flooding_base.models import Setting
from flooding_base.models import Map
from flooding_base.models import Site


log = logging.getLogger('nens.base.views')


#-------------------helper functions-----------------------------------
def get_connector_or_404(configuration_id):
    """Checks whether it's a database config (default, recommended), or a
    settings config

    returns connector if successful

    input: configuration_id (string)

    """
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    connector = configuration.getConnector()

    return connector


def get_and_set_is_standalone(request, setting=None):
    """Used to enable or disable the top bar on pages. The setting is
    stored in the session
    """
    if setting is not None:
        request.session['is_standalone'] = bool(int(setting))
    return request.session.get('is_standalone', True)


#-----------------------views -----------------------------------------
@login_required
def testdatabase(request, configuration_id):
    """Checks connection status of database connection, given configuration_id

    only for staff member!

    #todo: this function is still partly hard-coded for Jdbc2Ei
    """
    if not(request.user.is_staff):
        raise Http404

    is_standalone = request.GET.get('is_standalone', None)

    errormessage = ''
    configuration = Configuration.objects.get(pk=int(configuration_id))
    try:
        connector = configuration.getConnector()
    except:
        #geen DataSource ingesteld
        errormessage = _("No DataSource could be found for this "
                         "configuration, please configure a DataSource.")
    try:
        isAlive = connector.isAlive()
    except:
        isAlive = 'Connector is not reachable'
    try:
        data = connector.executeTest()
        dataCount = len(data)
        canExecuteQuery = True
    except:
        canExecuteQuery = False
        dataCount = -1
    #ei specific. getUrl must be called after execute, because execute
    #  can set/change the url
    try:
        url = connector.getUrl()
    except:
        url = 'could not connector.getUrl()'

    d = {'errormessage': errormessage,
         'configuration': configuration,
         'is_standalone': get_and_set_is_standalone(request,
                                                    is_standalone),
         'isAlive': isAlive,
         'canExecuteQuery': canExecuteQuery,
         'dataCount': dataCount,
         'url': url,
         'user': request.user,
         'breadcrumbs': [{'name': u'%s' % _('Database connection list'),
                          'url': reverse('testdatabase_list')},
                         {'name': u'%s' % _('Test database connection')}],
        }
    return render_to_response(
        'base/testdatabase.html',
        d,
        context_instance=RequestContext(request))


@login_required
def testdatabase_list(request):
    if not request.user.is_staff:
        raise Http404
    is_standalone = request.GET.get('is_standalone', None)
    breadcrumbs = [{'name': u'%s' % _('Database connection list')}]
    object_list = Configuration.objects.all()

    return render_to_response(
        'base/configuration_list.html',
        {'user': request.user,
         'is_standalone': get_and_set_is_standalone(
                request, is_standalone),
         'breadcrumbs': breadcrumbs,
         'object_list': object_list,
         },
        context_instance=RequestContext(request))


def get_filters(configuration_id):
    """queries "select * from filters" from Jdbc2Ei, from given
    configuration_id

    returns array of dictionary
    crashes if source does not exist
    """
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    datasource = configuration.get_datasource()
    if ((configuration.datasourcetype == Configuration.DATASOURCE_TYPE_EI)
        and datasource.usecustomfilterresponse):
        #beware! no errorchecking!
        #print datasource.customfilterresponse
        return eval(datasource.customfilterresponse)

    connector = configuration.getConnector()
    #get_connector_or_404(configuration_id)
    #dit zou moeten werken, maar het werkt niet.
    #data = connector.execute('select distinct id,name,parentid from filters;')
    columnnames = ['id', 'name', 'parentid']

    if configuration.datasourcetype == Configuration.DATASOURCE_TYPE_EI:
        data = connector.execute(
            'select distinct id,name,parentid from filters ' +
            'where issubfilter=1;',
            columnnames)

        update = connector.execute('select distinct id, name from filters ' +
                                   'where issubfilter=0;', columnnames)
        for i in range(len(update)):
            update[i]['parentid'] = None

        #now update the data
        data = data + update
    elif configuration.datasourcetype == Configuration.DATASOURCE_TYPE_DUMMY:
        data = connector.execute('get_filters')

    return data


def get_configurations(
    request,
    permission=GroupConfigurationPermission.PERMISSION_VIEW):
    """gets all configurations where the user has xxx permissions

    if request.session['configuration'] is filled, then filter the list of
    configs by that list too (the request.session['configuration'] is filled
    with configuration.id's]
    """
    user = request.user
    if user.is_authenticated():
        if user.is_staff:
            configurations = Configuration.objects.all()
            if 'configuration' in request.session:
                #extra filter
                configurations = configurations.filter(
                    id__in=request.session['configuration'])
            return configurations
        else:
            gcp_list = GroupConfigurationPermission.objects.filter(
                group__in=user.groups.all(), permission=permission)
    else:
        demogroup = Group.objects.get(name='demo group')
        gcp_list = GroupConfigurationPermission.objects.filter(
            group=demogroup, permission=permission)
    if 'configuration' in request.session:
        #extra filter
        gcp_list = gcp_list.filter(
            configuration__in=request.session['configuration'])
    return [gcp.configuration for gcp in gcp_list]


def check_permission_configuration(user, configuration, permission):
    """Checks permission for user, configuration, permission"""
    if user.is_staff:
        return True
    if GroupConfigurationPermission.objects.filter(
        group__in=user.groups.all, permission=permission):
        return True
    else:
        return False


def get_default_extent(request):
    """
    Get (bundled) extent for the sum of configurations available for current
    user
    """
    configurations = get_configurations(request)
    east, west, north, south = [None] * 4
    for c in configurations:
        if east is None:
            east = c.coords_e
        if west is None:
            west = c.coords_w
        if north is None:
            north = c.coords_n
        if south is None:
            south = c.coords_s
        if c.coords_e > east:
            east = c.coords_e
        if c.coords_w < west:
            west = c.coords_w
        if c.coords_n > north:
            north = c.coords_n
        if c.coords_s < south:
            south = c.coords_s

    result = {}
    result['east'] = east
    result['west'] = west
    result['north'] = north
    result['south'] = south
    return result


#-----------------------the services ----------------------------------
def service_get_configurations(request):
    """returns a list of configurations from the database in json"""
    data = serializers.serialize("json", Configuration.objects.all())
    return HttpResponse(data)


def service_get_filters(request, configuration_id):
    """returns "select * from filters" from Jdbc2Ei, from given
    configuration_id"""

    data = get_filters(configuration_id)
    #add configurationid
    for row in data:
        row['configurationid'] = configuration_id
    return render_to_response('base/filter.json',
                              {'data': data})


@cache_control(no_cache=True, must_revalidate=True, no_store=True,
               post_check="o", pre_check="o", max_age=0)
def service_get_auth_filters(
    request, permission=GroupConfigurationPermission.PERMISSION_VIEW):
    """returns filters from 1 or more configurations

    if there is 1 configuration, the filter is placed in the
    root. Else, the root consists of the configuration names
    """

    configurations = get_configurations(request)
    if len(configurations) == 1:
        try:
            result_filters = get_filters(configurations[0].id)
        except:
            result_filters = [{'parentid': None,
                               'id': None,
                               'name': _('datasource offline'),
                               'is_filter': False}]
        #add configurationid
        for row in result_filters:
            row['configurationid'] = configurations[0].id
            row['is_filter'] = True
        return HttpResponse(json.dumps(result_filters),
                            mimetype='application/json')
    elif len(configurations) > 1:
        #create root items
        result_filters = [{'id': 'configuration_%d' % c.id,
                           'name': c.name, 'parentid': None,
                           'configurationid': c.id,
                           'is_filter': False, 'west': c.coords_w,
                           'east': c.coords_e, 'south': c.coords_s,
                           'north': c.coords_n} for c in configurations]
        for c in configurations:
            try:
                filters_single = get_filters(c.id)
            except:
                filters_single = [{'parentid': None,
                                   'id': None,
                                   'name': _('datasource offline'),
                                   'is_filter': False}]
            #  append to result_filters, while replacing parentid: None to
            # correct parentid
            for row in filters_single:
                if row['parentid'] is None:
                    row['parentid'] = 'configuration_%d' % c.id
                row['configurationid'] = c.id
                row['is_filter'] = True
            result_filters.extend(filters_single)

        response = HttpResponse(json.dumps(result_filters),
                                mimetype='application/json')
    else:
        response = HttpResponse(json.dumps([]),
                                mimetype='application/json')
    response['Pragma'] = "no-cache"
    return response


def service_get_locations(request, configuration_id, filter_id):
    """get locations given configuration_id and filter_id

    return id, name (from filters)
    x, y, parentid (from locations)

    """
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    connector = configuration.getConnector()

    if configuration.datasourcetype == Configuration.DATASOURCE_TYPE_EI:
        #some 'hacking' is needed to get the desired result from Jdbc...
        #first get the locations from filters
        q = ('select distinct locationid from filters ' + \
             'where id=\'%s\' order by location') % filter_id
        locations_from_filters = connector.execute(q, ['id'])
        #then join the the locations from locations, to get all location data
        location_array = []
        parent_dict = {}

        location_all_dict = cache.get('all_locations' + str(configuration_id))
        if location_all_dict == None:
            query = ('select id, name, parentid, longitude, latitude from '
                     'locations order by name')
            all_locations = connector.execute(
                query, ['id', 'name', 'parentid', 'longitude', 'latitude'],
                debug=settings.DEBUG)

            location_all_dict = {}
            for row in all_locations:
                location_all_dict[row['id']] = row

            cache.set('all_locations' + str(configuration_id),
                      location_all_dict, 300)

        for row in locations_from_filters:
            id = row['id']
            result = location_all_dict[id]
            result['in_filter'] = 1
            location_array.append(result)
            parent_dict[result['id']] = True

        # loop again to find missing parents, and again, and again until all
        # parents are found added = True # Unused
        for row in location_array:
            id = row['parentid']
            if not(id is None or id in parent_dict):

                result = location_all_dict[id]
                result['in_filter'] = 0
                location_array.append(result)
                parent_dict[id] = True

    elif configuration.datasourcetype == Configuration.DATASOURCE_TYPE_DUMMY:
        location_array = connector.execute('get_locations')

    #print location_dict
    return render_to_response('base/location.json', {'data': location_array})


def service_get_parameters(request, configuration_id, filter_id,
                           location_id=None):
    """get parameters given configuration_id and filter_id"""
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    connector = configuration.getConnector()

    #first get the locations from filters
    query = ('select distinct parameterid, parameter '
             'from filters where id=\'%s\' ') % filter_id
    if location_id != None:
        query = query + ' and locationid =\'%s\' ' % location_id
    query = query + 'order by parameter'
    parameters = connector.execute(query, ['parameterid', 'parameter'])
    return render_to_response('base/parameter.json', {'data': parameters})


def service_get_location(request, configuration_id, location_id):
    """get location given configuration_id and location_id"""
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    connector = configuration.getConnector()

    #first get the locations from filters
    query = ('select name, id, parentid, description, shortname, tooltiptext, '
             'x, y, z, longitude, latitude, icon from locations '
             'where id=\'%s\'') % location_id
    columnnames = ['name', 'id', 'parentid', 'description', 'shortname',
                   'tooltiptext', 'x', 'y', 'z', 'longitude', 'latitude',
                   'icon']
    parameters = connector.execute(query, columnnames)

    return render_to_response('base/location_detail.json',
                              {'data': parameters})


def service_get_timeseries(request, configuration_id):
    """returns timeseries in json/html/image format, fields: timestamp, value,
    flag, detection, comments

    graph = jdbc graph

    todo: check input

    requires GET with the following options:
    filterid: i.e. ALM_RIO
    locationid: i.e. ALM_219/1
    parameterid: i.e. h.niveau.max
    (optional) format: {'json','html','graph','graph2'}
    (optional) dtstart, dtend: in iso8601 format, i.e. 2009-02-25

    """
    DATEFORMAT = '%Y-%m-%d %H:%M:%S'
    if request.method == 'GET':
        #get connector
        configuration = get_object_or_404(Configuration, pk=configuration_id)
        connector = configuration.getConnector()

        #get parameters
        q = request.GET
        filter_id = q.get('filter_id')
        location_id = q.get('location_id')
        parameter_id = q.get('parameter_id')
        dtstart_str = q.get('dtstart', None)
        dtend_str = q.get('dtend', None)
        format = q.get('format', 'json')
        graphwidth = int(q.get('graphwidth', 700))
        graphheight = int(q.get('graphheight', 300))

        items_per_page = int(q.get('items_per_page', '10'))
        page_nr = int(q.get('page_nr', '1'))

        #prepare query
        dtstart = None
        dtend = None
        query_time = ''
        if dtstart_str is not None and dtend_str is not None:
            #no place for sql injections here...
            dtstart = iso8601.parse_date(dtstart_str)
            dtend = iso8601.parse_date(dtend_str)
            query_time = " and time between '%s' and '%s'" % (
                dtstart.strftime(DATEFORMAT), dtend.strftime(DATEFORMAT))

        if (format == 'json'
            or format == 'html'
            or format == 'csv'
            or format == 'graph2'):
            base_query = ("select time,value,flag,detection,comment "
                          "from timeseries")
            columnnames = ['time', 'value', 'flag', 'detection', 'comment']
            date_fields = ['time']
            binary_fields = None
            query_extra = ''
        elif format == 'graph':
            base_query = "select graph from timeseriesgraphs"
            columnnames = ['graph']
            date_fields = None
            binary_fields = ['graph']
            query_extra = ' and width=%d and height=%d' % (graphwidth,
                                                           graphheight)

        query = ("%s where filterid='%s' and locationid='%s' "
                 "and parameterid='%s'%s%s") % (base_query, filter_id,
                                                location_id, parameter_id,
                                                query_time, query_extra)

        #run query
        result = connector.execute(query, columnnames,
                                   date_fields=date_fields,
                                   binary_fields=binary_fields)

        #prepare output
        title = ''
        #period = '%s: %s' % (_('Period'), 'period string')

        #output
        if format == 'json':
            return render_to_response('base/timeseries.json', {'data': result})
        elif format == 'html':
            paginator = Paginator(result, items_per_page)
            extra_fields = {'action': 'get_timeseries',
                            'configuration_id': configuration.id,
                            'format': 'html',
                            'filter_id': filter_id,
                            'location_id': location_id,
                            'parameter_id': parameter_id,
                            'dtstart': dtstart_str,
                            'dtend': dtend_str,
                            }

            return render_to_response(
                'base/timeseries.html',
                {'title': title,
                 'datacolumns': columnnames,
                 'configuration_id': configuration.id,
                 'filter_id': filter_id,
                 'location_id': location_id,
                 'parameter_id': parameter_id,
                 'dtstart': dtstart_str,
                 'dtend': dtend_str,

                 #for digg-paginator
                 'paginator': paginator,
                 'page': paginator.page(page_nr),
                 'extra_fields': extra_fields,
                 },
                context_instance=RequestContext(request))
        elif format == 'graph':
            response = HttpResponse(result[0]['graph'])
            response['Content-type'] = 'image/png'
            return response
        elif format == 'graph2':
            return chart_timeseries(request, result)
        elif format == 'csv':
            if dtstart is not None and dtend is not None:
                filename = '%s_%s_%s_%s_%s-%s.csv' % (configuration.name,
                                                      filter_id,
                                                      location_id,
                                                      parameter_id,
                                                      dtstart,
                                                      dtend)
            else:
                filename = '%s_%s_%s_%s_all.csv' % (configuration.name,
                                                    filter_id,
                                                    location_id,
                                                    parameter_id)
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename="%s"' % (
                filename)
            writer = csv.writer(response)
            writer.writerow(['time', 'value', 'flag', 'detection', 'comment'])
            for row in result:
                writer.writerow([row['time'], row['value'], row['flag'],
                                 row['detection'], row['comment']])
            return response


# TODO: apparently unused!
def service_get_current_observation(request, configuration_id):
    """
    Returns latest values in json with:
    * waterlevel (m)
    * rainfall (mm/h)
    * rainfall_day (mm/day)
    * groundwaterlevel (m)
    * pump_discharge (m3/s, -)
    * drain_capacity_used (percent, -)
    * timestamp (-)
    """
    #get connector
    configuration = get_object_or_404(Configuration, pk=configuration_id)
    connector = configuration.getConnector()

    qd = request.GET
    #make tuples of (filter, location, parameter)
    water_level_lp = (
        qd['water_level_f'],
        qd['water_level_l'],
        qd['water_level_p'])
    rainfall_hour_lp = (
        qd['rainfall_hour_f'],
        qd['rainfall_hour_l'],
        qd['rainfall_hour_p'])
    groundwater_level_lp = (
        qd['groundwater_level_f'],
        qd['groundwater_level_l'],
        qd['groundwater_level_p'])
    pump_discharge_lp = (
        qd['pump_discharge_f'],
        qd['pump_discharge_l'],
        qd['pump_discharge_p'])
    drain_capacity_used_lp = (
        qd['drain_capacity_used_f'],
        qd['drain_capacity_used_l'],
        qd['drain_capacity_used_p'])

    now = datetime.datetime.now()
    dt_start = now - datetime.timedelta(days=7)
    dt_end = now + datetime.timedelta(days=1)
    dt_format = '%Y-%m-%d %H:%M:%S'

    dt_start_str = dt_start.strftime(dt_format)
    dt_end_str = dt_end.strftime(dt_format)
    dt_yesterday_str = (now - datetime.timedelta(days=1)).strftime(dt_format)
    dt_now_str = now.strftime(dt_format)

    #get timeseries (it must be sorted on time)
    query_base = ("select time, value, flag from timeseries where "
                  "filterid='%s' and locationid='%s' and "
                  "parameterid='%s' and time between '%s' and '%s'")
    query_stats = ("select mean, min, max, sum from timeseriesstats where "
                   "filterid='%s' and locationid='%s' and parameterid='%s' "
                   "and time between '%s' and '%s'")
    column_names_base = ['time', 'value', 'flag']
    column_names_stats = ['mean', 'min', 'max', 'sum']

    #timeseries for water_level
    query = query_base % (water_level_lp + (dt_start_str, dt_end_str))
    water_level_ts = connector.execute(query,
                                       column_names=column_names_base,
                                       date_fields=['time'])
    if water_level_ts and water_level_ts != -2:
        water_level_value = {
            'datetime': water_level_ts[-1]['time'].strftime(dt_format),
            'value': water_level_ts[-1]['value']}
    else:
        water_level_value = {'datetime': None, 'value': None}

    #timeseries for rainfall_hour
    query = query_base % (rainfall_hour_lp + (dt_start_str, dt_end_str))
    rainfall_hour_ts = connector.execute(query,
                                         column_names=column_names_base,
                                         date_fields=['time'])
    if rainfall_hour_ts and rainfall_hour_ts != -2:
        rainfall_hour_value = {
            'datetime': rainfall_hour_ts[-1]['time'].strftime(dt_format),
            'value': rainfall_hour_ts[-1]['value']}
    else:
        rainfall_hour_value = {'datetime': None, 'value': None}

    #day value for rainfall
    query = query_stats % (rainfall_hour_lp + (dt_yesterday_str, dt_now_str))
    rainfall_stats_ts = connector.execute(query,
                                          column_names=column_names_stats)
    if rainfall_stats_ts and rainfall_stats_ts != -2:
        rainfall_day_value = rainfall_stats_ts[0]['sum']
    else:
        rainfall_day_value = None

    #timeseries for groundwater_level
    query = query_base % (groundwater_level_lp + (dt_start_str, dt_end_str))
    groundwater_level_ts = connector.execute(query,
                                             column_names=column_names_base,
                                             date_fields=['time'])
    if groundwater_level_ts and groundwater_level_ts != -2:
        groundwater_level_value = {
            'datetime': groundwater_level_ts[-1]['time'].strftime(dt_format),
            'value': groundwater_level_ts[-1]['value']}
    else:
        groundwater_level_value = {'datetime': None, 'value': None}

    #timeseries for pump_discharge
    query = query_base % (pump_discharge_lp + (dt_start_str, dt_end_str))
    pump_discharge_ts = connector.execute(query,
                                             column_names=column_names_base,
                                             date_fields=['time'])
    if pump_discharge_ts and pump_discharge_ts != -2:
        pump_discharge_value = {
            'datetime': pump_discharge_ts[-1]['time'].strftime(dt_format),
            'value': pump_discharge_ts[-1]['value']}
    else:
        pump_discharge_value = {'datetime': None, 'value': None}

    #timeseries for drain_capacity_used
    query = query_base % (drain_capacity_used_lp + (dt_start_str, dt_end_str))
    drain_capacity_used_ts = connector.execute(query,
                                             column_names=column_names_base,
                                             date_fields=['time'])
    if drain_capacity_used_ts and drain_capacity_used_ts != -2:
        drain_capacity_used_value = {
            'datetime': drain_capacity_used_ts[-1]['time'].strftime(dt_format),
            'value': drain_capacity_used_ts[-1]['value']}
    else:
        drain_capacity_used_value = {'datetime': None, 'value': None}

    response_dict = {
        'id': configuration_id,
        'name': configuration.name,
        'water_level': water_level_value,
        'rainfall_hour': rainfall_hour_value,
        'rainfall_day': rainfall_day_value,
        'groundwater_level': groundwater_level_value,
        'pump_discharge': pump_discharge_value,
        'drain_capacity_used': drain_capacity_used_value,
        'timestamp': dt_now_str,
        }

    return HttpResponse(json.dumps(response_dict),
                        mimetype='application/javascript')


def service_set_current_subapplication(request, site_name, js_app_name):
    """
    stores current subapplication in session. returns current sa jsname in json
    """
    sa = SubApplication.objects.get(type=SubApplication.NAME2TYPE[js_app_name])

    current_subapplication = request.session.get('current_subapplication', {})
    if not current_subapplication:
        current_subapplication = {}
    current_subapplication[site_name] = sa
    request.session['current_subapplication'] = current_subapplication
    try:
        log.debug('setting current_subapplication: %s',
                  str(current_subapplication))
    except NameError:
        pass
    result = {'app_name': sa.get_subapplication_jsname()}
    return HttpResponse(json.dumps(result),
                        mimetype='application/json')


def service_uberservice(request):
    """wrapper for other services, gets arguments from GET

    todo: alle inputs checken

    """
    if request.method == 'GET':
        q = request.GET

        action = q.get('action')
        #some sort of switch-case.. if done with a dictionary,
        #each parameter is evaluated before execution and some
        #functions will not work...
        if action == 'get_filters':
            return service_get_filters(request, q.get('configuration_id'))
        if action == 'get_auth_filters':
            permission = q.get('permission',
                               GroupConfigurationPermission.PERMISSION_VIEW)
            return service_get_auth_filters(request, permission=permission)
        elif action == 'get_configurations':
            return service_get_configurations(request)
        elif action == 'get_locations':
            configuration_id = q.get('configuration_id')
            filter_id = q.get('filter_id')
            return service_get_locations(request, configuration_id, filter_id)
        elif action == 'get_parameters':
            configuration_id = q.get('configuration_id')
            filter_id = q.get('filter_id')
            location_id = q.get('location_id', None)
            return service_get_parameters(request, configuration_id,
                                          filter_id, location_id)
        elif action == 'get_applications':
            return service_get_applications(request)
        elif action == 'get_timeseries':
            configuration_id = q.get('configuration_id')
            return service_get_timeseries(request, configuration_id)
        elif action == 'get_current_observation':
            configuration_id = q.get('configuration_id')
            return service_get_current_observation(request, configuration_id)
        elif action == 'set_current_subapplication':
            js_app_name = q.get('app_name')
            site_name = q.get('site_name')
            return service_set_current_subapplication(request, site_name,
                                                      js_app_name)
    raise Http404


def chart_timeseries(request, data):
    """Draws a timeseries chart

    data=array of dictionaries, each dictionary must contain keys: time, value
    """

    fig = Figure()
    ax = fig.add_subplot(111)
    x = []
    y = []
    #now = datetime.datetime.now()
    #delta = datetime.timedelta(days=1)

    for row in data:
        x.append(row['time'])
        y.append(row['value'])

    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    ax.grid(True)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def service_get_applications(request):
    """gets available applications, i.e. lizard-report, lizard-flooding"""
    apps = []
    try:
        from lizard.report.models import Report
        Report  # pyflakes
        apps.append({'id': 'lizard-report',
                     'name': _('Lizard-report'),
                     'url': reverse('report_url')})
    except ImportError:
        pass

    try:
        from lizard.flooding.models import Scenario
        Scenario  # pyflakes
        apps.append({'id': 'lizard-flooding',
                     'name': _('Lizard-flooding'),
                     'url': reverse('flooding_url')})
    except ImportError:
        pass
    return render_to_response('lizard/application_list.json',
                              {'apps': apps})


def gui(request):
    """
    Shows GUI main page

    Settings from base.setting

    request.GET can have optional parameter configuration (with configuration
    name, non case sensitive as value), the configuration.id is stored a list
    in request.session['configuration']. Otherwise
    request.session['configuration'] is deleted
    """

    USE_GOOGLEMAPS = bool(int(Setting.objects.get(key='USE_GOOGLEMAPS').value))
    USE_OPENSTREETMAPS = bool(int(Setting.objects.get(
                key='USE_OPENSTREETMAPS').value))
    GOOGLEMAPS_KEY = Setting.objects.get(key='GOOGLEMAPS_KEY').value

    #default urls
    url_root = reverse('root_url')

    if request.GET.__contains__('clear_session'):
        request.session.clear()

    if 'configuration' in request.session:
        log.debug('request session has key "configuration"')
        del request.session['configuration']

    if 'current_subapplication' in request.session:
        session_subapp = request.session['current_subapplication']
        if not isinstance(session_subapp, dict):
            #old version didn't have a dictionary and would raise an error!
            request.session.clear()
            session_subapp = {}
        log.debug('request session has key "current_subapplication": %s',
                  str(session_subapp))
    else:
        session_subapp = {}

    configuration_value = request.GET.get('configuration', '')
    if configuration_value != '':
        log.debug('configuration_value !=\'\'')
        try:
            configuration = Configuration.objects.get(
                name__iexact=configuration_value)
            request.session['configuration'] = [configuration.id]
        except Configuration.DoesNotExist:
            #print 'does not exist'
            if 'configuration' in request.session:
                del request.session['configuration']
        except Configuration.MultipleObjectsReturned:
            if 'configuration' in request.session:
                del request.session['configuration']

    site = Site.objects.get(name='default_site')

    if site.favicon_image:
        url_favicon = url_root + site.favicon_image.url
    else:
        url_favicon = url_root + Setting.objects.get(key='URL_FAVICON').value

    if site.topbar_image:
        url_topbar = url_root + site.topbar_image.url
    else:
        url_topbar = url_root + Setting.objects.get(key='URL_TOPBAR').value

    request.session['configuration'] = [c.id for c in
                                        site.configurations.all()]

    extent = {'east': site.coords_e, 'west': site.coords_w,
              'north': site.coords_n, 'south': site.coords_s}

    RESTRICTMAP = bool(int(Setting.objects.get(key='RESTRICTMAP').value))

    javascript_parameters = json.dumps({
            'root_url': reverse('root_url'),
            'sitename': site.name,
            'uberservice_url': reverse('base_service_uberservice'),
            'use_googlemaps': USE_GOOGLEMAPS,
            'use_openstreetmaps': USE_OPENSTREETMAPS,
            'restrictmap': RESTRICTMAP,
            'extent': extent,
            'pyramid_parameters_url': reverse('pyramids_parameters'),
            'raster_server_url': settings.RASTER_SERVER_URL,
        })

    # If there is a 'preload_scenario' in the session (from a link
    # that goes directly to a scenario, we place it in the template as
    # JSON. Then we clear it from the session, otherwise the site will
    # keep going to that scenario!
    preload_scenario = json.dumps(
        request.session.get('preload_scenario', None))
    request.session['preload_scenario'] = None

    request_language = translation.get_language_from_request(request)
    if request_language is None:
        request_language = settings.LANGUAGE_CODE
    if request_language == 'nl':
        next_language = 'en'
    elif request_language == 'en':
        next_language = 'nl'
    else:
        next_language = request_language

    return render_to_response(
        'gui/index.html', {
            'url_topbar': url_topbar,
            'USE_GOOGLEMAPS': USE_GOOGLEMAPS,
            'GOOGLEMAPS_KEY': GOOGLEMAPS_KEY,
            'javascript_parameters': javascript_parameters,
            'user': request.user,
            'USE_OPENSTREETMAPS': USE_OPENSTREETMAPS,
            'RESTRICTMAP': RESTRICTMAP,
            'url_favicon': url_favicon,
            'preload_scenario': preload_scenario,
            'request_language': request_language,
            'next_language': next_language,
            },
        context_instance=RequestContext(request))


def gui_config(request):
    """Returns config.js, with customized fields"""
    site_value = request.GET.get('site', '')
    if site_value == '':
        site = Site.objects.filter(
            name__iexact='default_site').order_by('id')[0]
    else:
        try:
            site = Site.objects.get(name__iexact=site_value)
        except Site.DoesNotExist:
            site = Site.objects.filter(
                name__iexact='default_site').order_by('id')[0]
    map_list = Map.objects.filter(site=site)

    wms_bounds = None
    user_zoom = None
    if 'mis' in site.get_subapplication_jsnames_str():
        from lizard.mis_nepal.models import Country, District
        country = Country.objects.all()
        b = country.extent()
        bound = [0, 0, 0, 0]
        bound[0] = b[0] - (b[2] - b[0]) / 5
        bound[1] = b[0] - (b[3] - b[1]) / 5
        bound[2] = b[0] + (b[2] - b[0]) / 5
        bound[3] = b[0] + (b[3] - b[1]) / 5
        wms_bounds = bound
        user_zoom = wms_bounds
        if not request.user.is_anonymous():
            districts = District.objects.filter(
                userdistrict__user=request.user)
            if districts.count() > 0:
                user_zoom = districts.extent()

    return render_to_response('gui/config.js', {
        'map_list': map_list,
        'user_zoom': user_zoom,
        'wms_bounds': wms_bounds,
        },
        context_instance=RequestContext(request))


def gui_translated_strings(request):
    """Returns translated_strings.html, with translated strings"""
    request_language = translation.get_language_from_request(request)
    if request_language == 'nl':
        translated_strings = 'gui/translated_strings.html'
    else:
        translated_strings = 'gui/translated_strings_EN.html'

    return render_to_response(translated_strings,
                              context_instance=RequestContext(request))


def help(request):
    """
    This method renders the help-page.
    """
    # TODO: move to base?
    return render_to_response('gui/help.html',
                              {},
                              context_instance=RequestContext(request))


def userconfiguration(request):
    """
    This method renders userconfiguration-page.
    """
    # TODO: move to base?
    return render_to_response(
        'gui/configuration.html',
        {},
        context_instance=RequestContext(request))
