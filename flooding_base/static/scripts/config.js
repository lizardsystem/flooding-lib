
console.log('start laden config.js');


var fews_parameters_on_location = true;

var isomorphicDir="../weblib/isomorphic/"; // abs path to isomorphic, needed to locate SmartClient CSS
var locationLizardFewsData = '../../service/';
var locationLizardData = '../lizard/service/';
var locationFloodingData = '../../flooding/service/';

var lizardKbFloodPngDirectory="../flooding/results/";
var settings = {}
settings.useImageService = true;


var cross_site_scripting_results = false;
var helpPage="help.html"

if (cross_site_scripting_results) {
    var settingDataTransport = "scriptInclude";
} else {
    var settingDataTransport = "xmlHttpRequest";
}

custom_layers = new Array();

custom_layers[0] = new OpenLayers.Layer.WMS("top10 lokaal", "http://192.168.0.21:8080/geoserver/wms", ///gwc/service toeveogen voor geowebcache
    {
        height: '512',
        width: '512',
        layers: 'waternet',
        styles: '',
        srs: 'EPSG:4326',
        //maxResolution: 180/512,
        format: 'image/png',
        tiled: 'true'
    }, {
        buffer: 0,
        reproject: true
});


var lizardDataDirectory="../flooding/dataserver/";  //  http://192.168.0.21:8082


console.log('klaar laden fconfig.js');
