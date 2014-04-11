/* global console, dat, L, layers, styles, $ */
/* jshint strict: false */

var limits = ':-5:15';

function updateMode(value){
  var url;
  if (value == 'Elevation') {
    background.setValue('None');
    layern.setValue('elevation');
    style.setValue('terrain');
    effect.setValue('None');
    statistics.setValue('None');
  } else if (value == 'Landuse') {
    background.setValue('None');
    layern.setValue('landuse');
    style.setValue('landuse');
    effect.setValue('None');
    statistics.setValue('Pie');
  } else if (value == 'Waterlevel') {
    background.setValue('None');
    layern.setValue('elevation');
    style.setValue('drought');
    effect.setValue('Waterlevel');
    statistics.setValue('Curve');
  } else if (value == 'Shade') {
    background.setValue('Street');
    layern.setValue('elevation');
    style.setValue('transparent');
    effect.setValue('Shade');
    statistics.setValue('None');
  }
}

function updateBackground(value){
  var url;
  if (value == 'Street') {
    url = 'http://geodata.nationaalgeoregister.nl/';
    url += 'tms/1.0.0/brtachtergrondkaart/{z}/{x}/{y}.png';
    base.setUrl(url);
    if (!map.hasLayer(base)) {
      map.addLayer(base);
    }
  } else if (value == 'Image') {
    url = 'http://geodata1.nationaalgeoregister.nl/';
    url += 'luchtfoto/tms/1.0.0/luchtfoto/EPSG28992/{z}/{x}/{y}.jpeg';
    base.setUrl(url);
    if (!map.hasLayer(base)) {
      map.addLayer(base);
    }
  } else {
    if (map.hasLayer(base)) {
      map.removeLayer(base);
    }
  }
}

function updateLayer(value){
  pyramid.setParams({layers: value});
  reloadStatistics();
}

function updateStyle(){
  pyramid.setParams({styles: style.getValue() + limits });
  reloadStatistics();
}

function updateOpacity(value){
  pyramid.setOpacity(value);
}

function updateEffect(){
  var params;
  if (effect.getValue() == 'Waterlevel') {
    params = {effects: 'drought:0:' + waterlevel.getValue()};
  } else if (effect.getValue() == 'Shade') {
    params = {effects: 'shade:0:' + shade.getValue()};
  } else {
    params = {effects: ''};
  }
  pyramid.setParams(params);
}

function rescale(){
  var url = '/wms?request=getlimits&layers=' + layern.getValue();
  url += '&width=16&height=16&srs=epsg:4326&bbox=' + map.getBounds().toBBoxString();
  $.getJSON(url, function(data) {
    limits = ':' + data[0][0] + ':' + data[0][1];
    updateStyle();
  });
}

function release(){
  limits = '';
  updateStyle();
}

function labelFormatter(label, series) {
  return "<div style='font-size:8pt;color:white;'>" + Math.round(series.percent) + "%</div>";
}

function updateGraph(data){
  if (statistics.getValue() == 'Curve') {
    $.plot("#graph", data);
  } else {
    $.plot('#graph', data[0], {
      series: {
        pie: {
          show: true,
          radius: 1,
          label: {
            show: true,
            radius: 2/3,
            formatter: labelFormatter,
            threshold: 0.1
          }
        }
      }
    });
  }
}

function reloadStatistics(){
  var url = '/wms?request=get';
  if (statistics.getValue() == 'Curve') {
    url += 'curves';
  } else {
    url += 'counts&styles=' + style.getValue();
  }
  url += '&layers=' + layern.getValue();
  url += '&width=256&height=256&srs=epsg:4326&bbox=' + map.getBounds().toBBoxString();
  $.getJSON(url, function(data) {
    updateGraph(data);
  });
}

function updateStatistics(value){
  if (value == 'None') {
    map.off('dragend', reloadStatistics);
    map.off('zoomend', reloadStatistics);
    map.off('moveend', reloadStatistics);
    map.off('resize', reloadStatistics);
    map.off('viewreset', reloadStatistics);
    $('#graphWrapper').css('display', 'none');
  } else {
    map.on('dragend', reloadStatistics);
    map.on('zoomend', reloadStatistics);
    map.on('moveend', reloadStatistics);
    map.on('resize', reloadStatistics);
    map.on('viewreset', reloadStatistics);
    $('#graphWrapper').css('display', 'block');
    reloadStatistics();
  }
}

function updateFeatureInfo(mouseEvent){
  var latlng = mouseEvent.latlng;
  var bounds = map.getBounds();
  var xMargin = (bounds.getEast() - bounds.getWest()) / 1000;
  var yMargin = (bounds.getNorth() - bounds.getSouth()) / 1000;
  var x1 = latlng.lng - xMargin;
  var x2 = latlng.lng + xMargin;
  var y1 = latlng.lat - yMargin;
  var y2 = latlng.lat + yMargin;
  var bbox = x1 + ',' + y1 + ',' + x2 + ',' + y2;
  var url = '/wms?request=getfeatureinfo&layers=' + layern.getValue();
  url += '&width=1&height=1&srs=epsg:4326&bbox=' + bbox;
  $.getJSON(url, function(data) {
    feature.setValue(data);
  })
  .fail(function(){
    feature.setValue('--');
  });
}

// Controls
var Controls = function() {
// Main
  this.mode = 'Elevation';
  this.opacity = 1;
  this.background = 'None';
// Layers
  this.layer = layers[0];
  this.style = 'terrain';
// Scaling
  this.rescale = rescale;
  this.release = release;
// Effects
  this.effect = 'None';
  this.waterlevel = -4;
  this.shade = 3;
// Info
  this.statistics = 'None';
  this.feature = '';
};

var controls = new Controls();
var gui = new dat.GUI();
// Main
var mode = gui.add(controls, 'mode', ['Elevation', 'Landuse', 'Waterlevel', 'Shade']);
var opacity = gui.add(controls, 'opacity', 0, 1);
var background = gui.add(controls, 'background', ['None', 'Street', 'Image']);
// Layers
var f1 = gui.addFolder('Layer settings');
var layern = f1.add(controls, 'layer', layers);
var style = f1.add(controls, 'style', styles);
// Scaling
f1.add(controls, 'rescale');
f1.add(controls, 'release');
// Effects
var f2 = gui.addFolder('Other Settings');
var effect = f2.add(controls, 'effect', ['None', 'Waterlevel', 'Shade']);
var waterlevel = f2.add(controls, 'waterlevel', -6, 14);
var shade = f2.add(controls, 'shade', 0, 10);
var statistics = f2.add(controls, 'statistics', ['None', 'Curve', 'Pie']);
// Info
var f3 = gui.addFolder('Feature info');
var feature = f3.add(controls, 'feature');

// Layers
mode.onChange(updateMode);
background.onChange(updateBackground);
layern.onChange(updateLayer);
style.onChange(updateStyle);
opacity.onChange(updateOpacity);
// Effects
effect.onChange(updateEffect);
waterlevel.onFinishChange(updateEffect);
shade.onFinishChange(updateEffect);
// Statistics
statistics.onChange(updateStatistics);

// Maps
var res = [
  3440.640,
  1720.320, 
  860.160, 
  430.080, 
  215.040, 
  107.520, 
  53.760, 
  26.880, 
  13.440, 
  6.720, 
  3.360, 
  1.680, 
  0.840, 
  0.420,
  0.210,
  0.105,
  0.0525,
  0.02625, 
  0.013125, 
  0.0065625, 
  0.00328125, 
  0.001640625, 
  0.0008203125, 
  0.00041015625, 
  0.000205078125
];
var RD = L.CRS.proj4js(
  'EPSG:28992', 
  '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812 +no_defs', 
  new L.Transformation(1, 285401.920, -1, 903401.920)
);
RD.scale = function(zoom) {
    return 1 / res[zoom];
};
var map = new L.Map('map', {
  continuousWorld: true,
  crs: RD,
  center: new L.LatLng(52.1, 5.2),
  zoom: 4
});
var base = new L.TileLayer(
  '', {
      tms: true,
      minZoom: 1,
      maxZoom: 13,
    }
);
var pyramid = L.tileLayer.wms("/wms", {
  layers: layern.getValue(),
  styles: style.getValue() + limits,
  format: 'image/png',
  transparent: true,
  minZoom: 1,
  maxZoom: 18,
  zIndex: 1
});
map.addLayer(pyramid);
map.on('click', updateFeatureInfo);
