console.log("Start of hover.js...");

/*global document, OpenLayers, console, appManager */

var hover = hover || (function () {
    "use strict";

    /* MapHoverControl, adapted from lizard-map */
    var map_tooltip_div;
    var map_div_id;
    var openlayers_map;

    var initialized = false;

    var init_map_tooltip = function (map, map_div_id) {
        if (initialized) {
            return;
        }

        openlayers_map = map;

        map_tooltip_div = document.createElement('div');
        map_tooltip_div.id = "map_tooltip";
        map_tooltip_div.setAttribute(
            "style",
            "position: absolute; top: 0; left: 0; borded: solid 1px #111; background-color: #fff; z-index: 2000; display: none;");


        var map_div = document.getElementById(map_div_id);

        map_div.appendChild(map_tooltip_div);

        initialized = true;
    };

    var show_map_tooltip = function(lon, lat, text) {
        // Callback, called from activeOverlay.hover_handler
        var lonlat = new OpenLayers.LonLat(lon, lat);
        var pixel = openlayers_map.getViewPortPxFromLonLat(lonlat);
        map_tooltip_div.style.top = pixel.y + 10;
        map_tooltip_div.style.left = pixel.x + 10;
        map_tooltip_div.style.padding = "3px";
        map_tooltip_div.style.border = "solid black 1px";
	map_tooltip_div.style.zIndex = 200800;
	map_tooltip_div.style.position = "absolute";
        //map_tooltip_div.textContent = text;
	map_tooltip_div.innerHTML = text;
	map_tooltip_div.style.display = "block";
	//map_tooltip_div.style.borderRadius = "10px";
	map_tooltip_div.style.border = "solid 1px #111";
	map_tooltip_div.style.backgroundColor = "#fff";
    };

    var make_callback = function (lon, lat) {
        return function (text) {
            show_map_tooltip(lon, lat, text);
        };
    };

    var map_tooltip = function (lon, lat) {
        if (appManager && appManager.selectedApp &&
            appManager.selectedApp.overlayManager &&
            appManager.selectedApp.overlayManager.activeOverlay &&
            appManager.selectedApp.overlayManager.activeOverlay.hover_handler) {
            appManager.selectedApp.overlayManager.activeOverlay.hover_handler(
                lon, lat, make_callback(lon, lat));
        }
    };

    var hide_map_tooltip = function () {
        map_tooltip_div.style.display = "none";
    };

    var MapHoverControl = OpenLayers.Class(OpenLayers.Control, {
        defaultHandlerOptions: {
            'delay': 500,
            'pixelTolerance': null,
            'stopMove': false
        },

        initialize: function (options) {
            this.handlerOptions = OpenLayers.Util.extend(
                {}, this.defaultHandlerOptions
            );
            OpenLayers.Control.prototype.initialize.apply(
                this, arguments
            );
            this.handler = new OpenLayers.Handler.Hover(
                this,
                {'pause': this.onPause, 'move': this.onMove},
                this.handlerOptions
            );
        },

        onPause: function (e) {
            var lonlat;
            lonlat = openlayers_map.getLonLatFromViewPortPx(e.xy);
            map_tooltip(lonlat.lon, lonlat.lat);
        },

        onMove: function (evt) {
            hide_map_tooltip();
        }
    });

    return {
        MapHoverControl: MapHoverControl,
        init_map_tooltip: init_map_tooltip
    };

})();

console.log("End of hover.js...");
