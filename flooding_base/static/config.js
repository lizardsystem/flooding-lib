
console.log('start laden config.js');

var settings = {}
//LIZARD-FEWS
settings.fews_parameters_on_location = true;//refreshen van parameter lijst als op locatie wordt gedrukt
settings.fews_default_period = 92; //standaard periode bij opstarten (in dagen terug vanaf nu)

//FLOODING
settings.useImageService = true;


var isomorphicDir="../static_media/weblib/isomorphic/"; // abs path to isomorphic, needed to locate SmartClient CSS

var locationLizardFewsData = '../service/';
var locationLizardData = '../lizard/service/';
var locationFloodingData = '../flooding/service/';
var lizardKbFloodPngDirectory="../flooding/results/";
var lizardDataDirectory="../flooding/dataserver/";
var locationMisData = '../mis/service/';




var custom_layers = new Array();

var mapStartLocation = {
    lat:51.5,
    lng:3.9,
    zoom: 10
}

var OpenLayers = OpenLayers || null;
if (OpenLayers!= null) {
    var offline_waternet = new OpenLayers.Layer.WMS("top10 lokaal", "http://192.168.0.23:8080/geoserver/wms",
    {
        height: '512',
        width: '512',
        layers: 'hhnk',
        styles: '',
        srs: 'EPSG:4326',
        //maxResolution: 180/512,
        format: 'image/png',
        tiled: 'true'
    }, {
        buffer: 0,
        reproject: true
    });

    //custom_layers.push(offline_waternet);

    var ahn = new OpenLayers.Layer.WMS("AHN", "http://ahn.geodan.nl/cgi-bin-noncache/edugis/mapserv.cgi?map=maps/edugis/hoogte.map&",
    {
        transparent: 'TRUE',
        height: '512',
        width: '512',
        layers: 'hoogtes',
        styles: '',
        srs: 'EPSG:4326',
        format: 'image/png'
    }, {
        buffer: 0,
        reproject: true
    });
    //custom_layers.push(ahn);
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
