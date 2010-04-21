# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404
from django.conf import settings

from lizard_visualization.symbol_manager import SymbolManager
from lizard_visualization.mapnik_legend import MapnikPointLegend
from lizard_visualization.models import ShapeDataLegend
from lizard_presentation.models import PresentationType


def get_symbol(request, symbol):
    """Get a symbol, which is optionally colored, rotated, scaled

    inputs: via GET
      - symbol: <filename_nopath> of symbol, e.g. plus_64.png
      - mask (optional): <filename_nopath> of mask, e.g. plus_64_mask.png
      - colorize (optional): <r,g,b> (float 0..1) e.g. 0.5,0.3,0.7
      - size (optional): <x,y>, cannot be 0 e.g. 32,32
      - rotate (optional): <angle> int in degrees, ccw e.g. 180
      - shadow_height (optional): <shadow_height> shadow height in pixels e.g. 2

    output: binary png, or exception if original does not exist
    """

    #get GET parameters
    q = request.GET

    kwargs = {}
    if q.__contains__('mask'):
        kwargs['mask'] = (q.get('mask'),)
    if q.__contains__('color'):
        kwargs['color'] = [float(v) for v in (q.get('color')).split(',')]
    if q.__contains__('size'):
        kwargs['size'] = [int(v) for v in (q.get('size')).split(',')]
    if q.__contains__('rotate'):
        kwargs['rotate'] = (int(q.get('rotate')),)
    if q.__contains__('shadow_height'):
        kwargs['shadow_height'] = (int(q.get('shadow_height')),)
    if q.__contains__('force'):
        kwargs['force'] = True

    #get absolute filename of symbol, crashes if symbol does not exist

    #enable this for debugging
    #set_console_logger()
    sm = SymbolManager(settings.SYMBOLS_DIR)
    filename_abs = sm.get_symbol_transformed(symbol, **kwargs)
    f = open(filename_abs, 'rb')
    result_bin = f.read()
    f.close()

    #generate response
    response = HttpResponse(result_bin)
    response['Content-type'] = 'image/png'
    return response


def legend_shapedata(request):
    """Draws a ShapeDataLegend

    input: GET['object_id']: ShapeDataLegend.id
    output: png image of the legend
    """
    shapedatalegend = get_object_or_404(ShapeDataLegend, pk=request.GET['object_id'])
    geo_type = shapedatalegend.presentationtype.geo_type
    if geo_type == PresentationType.GEO_TYPE_POINT:
        sm = SymbolManager(settings.SYMBOLS_DIR)
        mpl = MapnikPointLegend(shapedatalegend, sm)
        title, blocks = mpl.get_legend_data()

        return render_to_response('visualization/legend_shapedata_point.html',
                                  {'title': title, 'blocks': blocks})

    elif geo_type == PresentationType.GEO_TYPE_LINE:
        if shapedatalegend.id in [20,]:
            legend_data = [(100,'005bff'),\
                          (500,'00ebff'),\
                           (1000,'4dff00'),\
                           (5000,'fff100'),\
                           (20000,'ff4100')]

            return render_to_response('visualization/legend_shapedata_grid.html',
                                  {'title': shapedatalegend.name,
                                   'content': legend_data})

        else:

            sm = SymbolManager(settings.SYMBOLS_DIR)
            mpl = MapnikPointLegend(shapedatalegend, sm)
            title, blocks = mpl.get_legend_data()

            return render_to_response('visualization/legend_shapedata_point.html',
                                  {'title': title, 'blocks': blocks})

    elif geo_type == PresentationType.GEO_TYPE_POLYGON:
        sm = SymbolManager(settings.SYMBOLS_DIR)
        mpl = MapnikPointLegend(shapedatalegend, sm)
        title, blocks = mpl.get_legend_data()

        return render_to_response('visualization/legend_shapedata_point.html',
                                  {'title': title, 'blocks': blocks})

    elif geo_type == PresentationType.GEO_TYPE_GRID:

        if shapedatalegend.id in [9,11,13,21]:
            legend_data = [(0.00,'E1E1FE'),\
            (0.02,'D2D2FE'),\
            (0.10,'C2C3FE'),\
            (0.20,'B3B4FE'),\
            (0.30,'A3A5FE'),\
            (0.40,'9496FE'),\
            (0.50,'8486FE'),\
            (0.60,'7577FE'),\
            (0.70,'6668FE'),\
            (0.80,'5659FE'),\
            (0.90,'474AFE'),\
            (1.00,'373BFE'),\
            (1.10,'282CFE'),\
            (1.20,'2529F4'),\
            (1.30,'2125EA'),\
            (1.40,'1E22E0'),\
            (1.50,'1B1ED6'),\
            (1.60,'171ACC'),\
            (1.70,'1417C2'),\
            (1.80,'1114B8'),\
            (1.90,'0D10AE'),\
            (2.00,'0A0CA4'),\
            (2.10,'07099A'),\
            (2.20,'030590'),\
            (2.30,'000286')]

        elif shapedatalegend.id in [8,10,12,14]:

            legend_data = [(0,'FEE1E1'),\
            (0.02,'FED2D2'),\
            (0.1,'FEC3C2'),\
            (0.2,'FEB4B3'),\
            (0.3,'FEA5A3'),\
            (0.4,'FE9694'),\
            (0.5,'FE8684'),\
            (0.6,'FE7775'),\
            (0.7,'FE6866'),\
            (0.8,'FE5956'),\
            (0.9,'FE4A47'),\
            (1,'FE3B37'),\
            (1.1,'FE2C28'),\
            (1.2,'F42925'),\
            (1.3,'EA2521'),\
            (1.4,'E0221E'),\
            (1.5,'D61E1B'),\
            (1.6,'CC1A17'),\
            (1.7,'C21714'),\
            (1.8,'B81411'),\
            (1.9,'AE100D'),\
            (2,'A40C0A'),\
            (2.1,'9A0907'),\
            (2.2,'900503'),\
            (2.3,'860200')]
        elif shapedatalegend.id in [19]:
        #damage
            legend_data = [(0,'38A800'),\
            (1000,'3EA200'),\
            (2000,'449D00'),\
            (5000,'4B9700'),\
            (10000,'519200'),\
            (20000,'588C00'),\
            (30000,'5E8700'),\
            (40000,'648200'),\
            (50000,'6B7C00'),\
            (60000,'717700'),\
            (70000,'787100'),\
            (80000,'7E6C00'),\
            (90000,'856600'),\
            (100000,'8B6100'),\
            (200000,'915C00'),\
            (300000,'985600'),\
            (400000,'9E5100'),\
            (500000,'A54B00'),\
            (600000,'AB4600'),\
            (700000,'B14100'),\
            (800000,'B83B00'),\
            (900000,'BE3600'),\
            (1000000,'C53000'),\
            (2000000,'CB2B00'),\
            (3000000,'D22500'),\
            (4000000,'D82000'),\
            (5000000,'DE1B00'),\
            (6000000,'E51500'),\
            (7000000,'EB1000'),\
            (8000000,'F20A00'),\
            (9000000,'F80500'),\
            (10000000,'FF0000')]

        elif shapedatalegend.id in [18]:
        #casualties
            legend_data = [(0.01,'FFFF00'),\
            (0.1,'F9F603'),\
            (0.2,'F3EE07'),\
            (0.3,'EDE60B'),\
            (0.4,'E7DE0E'),\
            (0.5,'E2D512'),\
            (0.6,'DCCD16'),\
            (0.7,'D6C519'),\
            (0.8,'D0BD1D'),\
            (0.9,'CBB421'),\
            (1,'C5AC25'),\
            (1.2,'BFA428'),\
            (1.4,'B99C2C'),\
            (1.6,'B39430'),\
            (1.8,'AE8B33'),\
            (2,'A88337'),\
            (2.5,'A27B3B'),\
            (3,'9C733F'),\
            (3.5,'976A42'),\
            (4,'916246'),\
            (4.5,'8B5A4A'),\
            (5,'85524D'),\
            (6,'7F4A51'),\
            (7,'7A4155'),\
            (8,'743959'),\
            (9,'6E315C'),\
            (10,'682960'),\
            (12.5,'632064'),\
            (15,'5D1867'),\
            (17.5,'57106B'),\
            (20,'51086F'),\
            (25,'4C0073')]

        else:
            legend_data = [(str(c.value_in), c.get_htmlcolor_out() ) \
                           for c in shapedatalegend.color.valuevisualizermapfloatcolor_set.all()]

        return render_to_response('visualization/legend_shapedata_grid.html',
                                  {'title': shapedatalegend.name,
                                   'content': legend_data})

    #crash here


def uber_service(request):
    """Collection of all available services.

    This function calls the actual functions
    """
    q = request.GET
    action = q.get('action').lower()
    if action == 'get_symbol':
        symbol = q['symbol']
        return get_symbol(request, symbol)
    elif action == 'get_legend_shapedata':
        return legend_shapedata(request)

    raise Http404


def testmapping(request):
    shapedatalegend = get_object_or_404(ShapeDataLegend, pk=1)
    sm = SymbolManager(settings.SYMBOLS_DIR)
    mpl = MapnikPointLegend(shapedatalegend, sm)
    #mapnik_rules = mpl.get_rules()

    result = '%s %s %s' % (mpl.get_rule_name({'value': 0.0}),
                           mpl.get_rule_name({'value': 1.0}),
                           mpl.get_rule_name({'value': 20.0}),)

    return HttpResponse(result)
