try {
    var console = console || {};
    console.log = console.log || function() {} ;
} catch (e)	{}


console.log('start laden config.js');

var settings = {}
//LIZARD-FEWS
settings.fews_parameters_on_location = true;//refreshen van parameter lijst als op locatie wordt gedrukt
settings.fews_default_period = 92; //standaard periode bij opstarten (in dagen terug vanaf nu)

//FLOODING
settings.useImageService = true;


//var isomorphicDir="{{ STATIC_URL }}weblib/isomorphic/"; // abs path to isomorphic, needed to locate SmartClient CSS
var isomorphicDir="{{ STATIC_URL }}weblib/smartclient/9.0/isomorphic/"; // abs path to isomorphic, needed to locate SmartClient CSS
{% autoescape off %}
var locationLizardFewsData = '{% url "root_url" %}service/';
var locationLizardData = '{% url "root_url" %}lizard/service/';
var locationFloodingData = '{% url "root_url" %}flooding/service/';
var locationPresentationData = "{% url "root_url" %}presentation/service/";
var locationFlowData = "{% url "root_url" %}flow/service/";
var locationGisviewerData = "{% url "root_url" %}gisviewer/service/";
var locationMapviewerData =  '{% url "root_url" %}mapviewer/service/';

var lizardKbFloodPngDirectory = "{% url "root_url" %}flooding/results/";
var lizardDataDirectory = "{% url "root_url" %}flooding/dataserver/";

var locationMisData = "{% url "root_url" %}mis/service/";
var locationNhiData = "{% url "root_url" %}nhi/service/";
var custom_layers = new Array();



{% if user_zoom %}
user_zoom = new OpenLayers.Bounds({{user_zoom.0}},{{user_zoom.1}},{{user_zoom.2}},{{user_zoom.3}})
{% endif %}

{% if wms_bounds %}
wms_bounds = new OpenLayers.Bounds({{wms_bounds.0}},{{wms_bounds.1}},{{wms_bounds.2}},{{wms_bounds.3}})
max_extent = wms_bounds;
maxExtent = wms_bounds;
{% endif %}



var OpenLayers = OpenLayers || null;
if (OpenLayers) {
    var maplayer = new OpenLayers.Layer.WMS(ST_EMPTY,{
	isBaseLayer: true, reproject: false,
	maxExtent: new OpenLayers.Bounds(-20037508, -20037508, 20037508, 20037508.34),
        maxResolution: 156543.0339});

    {% for m in map_list %}
	{% if m.active %}
            var params = {
		{% if m.transparent %}
		    transparent: true,
		{% endif %}
		height: '512',
		width: '512',
		layers: '{{ m.layers }}',
		styles: '',
		singleTile: {% if m.tiled %}false{% else %}true{% endif %},
		format: 'image/png'};
            var options = {
		{% if m.is_base_layer %}{% else %}
		    visibility: false,
		{% endif %}
		isBaseLayer:{% if m.is_base_layer %}true{% else %}false{% endif %},
		buffer: 0,
		reproject: false,
		scales: [
		    1.40625, 
		    0.703125, 
		    0.3515625, 
		    0.17578125, 
		    0.087890625, 
		    0.0439453125,
		    0.02197265625, 
		    0.010986328125, 
		    0.0054931640625, 
		    0.00274658203125,
		    0.001373291015625, 
		    0.0006866455078125, 
		    0.00034332275390625,
		    0.000171661376953125, 
		    0.0000858306884765625, 
		    0.00004291534423828125,
		    0.00002145767211914062, 
		    0.00001072883605957031,
		    0.00000536441802978515, 
		    0.00000268220901489257]}; 
            
     	    var maplayer = new OpenLayers.Layer.WMS("{{ m.name }}", "{{ m.url }}", params, options);
            maplayer.projection = new OpenLayers.Projection('{{ m.srs}}');
            custom_layers.push(maplayer);
	{% endif %}
    {% endfor %}
}

var helpPage="help.html"

function getPopupSize(width_map, height_map) {

    var max_percentage_width =  0.7; //relative to map
    var max_percentage_height = 0.7; //relative to map


    var min_width = 250;
    var max_width = 630; //groter dan 630 lijkt opmaak problemen op te leveren
    var min_height = 250;
    var max_height = 500;

    var width = Math.round(Math.max(Math.min(max_percentage_width * width_map, max_width),min_width));
    var height = Math.round(Math.max(Math.min(max_percentage_height * height_map, max_height),min_height));

    return {width:width, height:height };
}


console.log('klaar laden config.js');
{% endautoescape %}
