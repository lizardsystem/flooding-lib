console.log('loading NMainScreenManager ...');

/****************************************************************/
/**** class:         NMainScreenManager                           */
/**** description:     This class represents the manager that is   */
/****               responsible for the action on and related   */
/****               to the main screen.                         */
/****************************************************************/


//function still worked on
isc.DataSource.create({
    ID:"ds_get_node",
    showPrompt:false,
    dataFormat:"json",
    dataURL: locationFloodingData,
    transformRequest : function (dsRequest) {
        if (dsRequest.operationType == "fetch") {
            var params = {action : 'get_nodes'};
            // combine paging parameters with criteria
            return isc.addProperties({}, dsRequest.data, params);
        }
    },
    recordXPath:"items",
    autoFetchData:false,
    autoDraw:false,
    fields:[
        {name:"id", primaryKey:true, hidden:true, type:"text"}
    ]
});

function NMainScreenManager(mainPane, settings) {
    this.mainPane = mainPane;

    // settings for the map
    settings = settings || {};
    this.initLat = settings.initLat || 52.5;
    this.initLng = settings.initLng || 5;
    this.initZoomlevel = settings.initZoomlevel || 9;
    this.extent = settings.extent || null; //this overrules initLat, initLng, initZoomlevel
    this.useOpenLayers = settings.useOpenLayers || true;
    this.mapDivName =  settings.mapDivName || "map";
    this.useGoogleLayers = settings.useGoogleLayers || false;
    this.useOpenStreetMap = settings.useOpenStreetMap || false;
    this.customLayers = settings.customLayers || [];
    this.restrictMap = settings.restrictMap || false;


    this.ispre_init = false;
    this.isinit = false;

    this.screen = [];
    this.screen[MAP] = null;
    this.screen[IFRAME] = null;
    this.screen[FRAME] = null;
}


/**** Pre initializing the NMainScreenManager ****/
NMainScreenManager.prototype.pre_init = function() {
    if (this.ispre_init) {
        return false;
    }

    this.screen = [];

    isc.Canvas.create({
        ID: "scMap",
        height: "100%",
        width: "100%",
        styleName:'canvasxxx',
        overflow: "hidden",
        contents: "<div id='map'></div>",
        autoDraw: true,
        layoutChildren: function(){
            //console.log('layout Childeren');
        }
    });

    isc.HTMLPane.create({
        ID: "scHTML",
        width: "100%",
        height: "100%",
        overflow:"auto",
        contentsType:"page",
        border: "none",
        autoDraw: false
    });


    isc.HTMLPane.create({
        ID: "scCanvas",
        width: "100%",
        height: "100%",
        border: "none",
        overflow:"auto",
        autoDraw: true // Note: needed for creating the pane object with all its content
    });

    /*isc.Canvas.create({
      ID: "scCanvas",
      width: "100%",
      height: "100%",
      overflow: "hidden",
      contents:"<div id = 'mmScreenSpan'> </div>",
      border: "none",
      autoDraw: false
      });*/

    this.screen[MAP] = scMap;
    this.screen[IFRAME] = scHTML;
    this.screen[FRAME] = scCanvas;

    for (var sc = 1; sc < this.screen.length;sc++) {
        this.screen[sc].init = false;
    }
    this.ispre_init = true;
    return true;
};

NMainScreenManager.prototype.getScreens = function() {
    this.pre_init();

    return [this.screen[MAP],this.screen[IFRAME], this.screen[FRAME]];
};


/**
 * function:
 */
NMainScreenManager.prototype.init = function() {
    if (this.isinit) {
        return false;
    }

    var screens = this.pre_init();
    //this.mainPane.addMembers(screens);

    this.isinit = true;
    return true;
};


/**
 * function:
 */
NMainScreenManager.prototype.destroy = function() {

};

/**
 * function:
 */
NMainScreenManager.prototype.setScreen = function(screenType, app) {
    this.init();
    //clean Iframe, because of hiding problems in I.E. of tables
    this.screen[IFRAME].setContentsURL("about:blank");

    for (var sc = 1; sc < this.screen.length;sc++) {
        if (sc != screenType) {
            this.mainPane.hideMember(this.screen[sc]);
        }
    }

    this.mainPane.showMember(this.screen[screenType]);
    this.mainPane.reflowNow();

    if (screenType == MAP && !this.screen[MAP].init) {
        this.initMap();
    } else if (screenType == IFRAME) {
        this.screen[screenType].setContentsURL(app.url);
    } else if (screenType == FRAME) {
        if (app.url) {
            this.screen[screenType].setContentsURL(app.url);
        } else {
            this.screen[screenType].setContents("-");
        }
    }
};

NMainScreenManager.prototype.getMap = function() {
    return this.map;
};

map = null;
/**** Initialize Openlayers Map for mainscreen ****/
NMainScreenManager.prototype.initMap = function() {
    this.init();

    var maxExtent = new OpenLayers.Bounds(-20037508, -20037508,
                                          20037508, 20037508.34);

    if (!this.map) {

        if (this.useOpenLayers) {

            // avoid pink tiles
            OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
            OpenLayers.Util.onImageLoadErrorColor = "transparent";

            document.getElementById(this.mapDivName).style.height = "100%";
            document.getElementById(this.mapDivName).style.width = "100%";
            document.getElementById(this.mapDivName).parentNode.style.width = "100%"; //needed for smartclient

            var onZoomEnd = function (e) {
                console.log(e.object.zoom);
                var map = e.object;
                var zoom = map.zoom;
                if (zoom > 6) {
                    map.setBaseLayer(map.layers[0]);
                }
                else {
                    map.setBaseLayer(map.layers[1]);
                }
            };

            var hover_control = new hover.MapHoverControl();

            var options = {
                projection: new OpenLayers.Projection("EPSG:900913"),
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                units: "m",
                numZoomLevels: 18,
                autoUpdateSize: true,
                //maxResolution: 156543.0339,
                maxExtent: maxExtent,
                controls: [
                    new OpenLayers.Control.NavToolbar(),
                    new OpenLayers.Control.Zoom(),
                    new OpenLayers.Control.LayerSwitcher({'ascending':false}),
                    hover_control
                ]
            };

            this.map = new OpenLayers.Map(this.mapDivName, options);
            this.map.isGoogleMaps = false;
            hover_control.activate();
            hover.init_map_tooltip(this.map, this.mapDivName);
            var layers;

            if (this.useGoogleLayers) {
                try {
                    layers = [
                        new OpenLayers.Layer.Google("Google Physical",{type: G_PHYSICAL_MAP,sphericalMercator: true,numZoomLevels: 20, displayInLayerSwitcher:false}),
                        new OpenLayers.Layer.Google("Google Hybrid",{type: G_HYBRID_MAP,sphericalMercator: true,numZoomLevels: 20}),
                        new OpenLayers.Layer.Google("Google Streets",{sphericalMercator: true,numZoomLevels: 20}),
                        new OpenLayers.Layer.Google("Google Satellite",{type: G_SATELLITE_MAP,sphericalMercator: true,numZoomLevels: 20})

                    ];
                    this.map.addLayers(layers);
                } catch (e) {
                    console.log("kan google lagen niet laden. " + e);
                }
            }

            if (this.useOpenStreetMap)
            {
                try {
		    layers = [new OpenLayers.Layer.OSM(
			"OpenStreetMap",
			"http://a.tile.openstreetmap.org/${z}/${x}/${y}.png",
			{buffer: 0} 
		    )];
		    this.map.addLayers(layers);
                    layers = [
                        new OpenLayers.Layer.OSM(
                            "OpenStreetMap NL",
                            "http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png",
                            {buffer: 0, tileOptions: {crossOriginKeyword: null}}
                        )];
                    this.map.addLayers(layers);
                    
                    
                }
                catch (e) {
                    console.log("kan Openstreet Map lagen niet laden." + e);
                }

            }

            // Add pdok layers
            try {
                layers = [
                    new OpenLayers.Layer.WMS("Top10NL", "http://geoserver6.lizard.net/geoserver/ipo_ror_flooding/wms", {layers: 'ipo_ror_flooding:pdok_top10_50', format: 'image/png'}, { minResolution: 0.42, numZoomLevels: 7 })
                ];
                this.map.addLayers(layers);
            } catch (e) {
                console.log("kan PDOK lagen niet laden.");
            }

            this.map.addLayers(this.customLayers);

            //init map
            console.log("kaart ingeladen. initialiseer kaart");

            try {
                var extent = new OBounds(this.extent);
                if (extent.validRect()) {
                    this.map.setCenter(extent.getCenterLonLat(),this.map.getZoomForExtent(extent));
                } else {
                    this.map.setCenter((new OpenLayers.LonLat(this.initLng, this.initLat)).transform(this.map.displayProjection, this.map.projection ) ,this.initZoomlevel, false, true);
                }
            } catch(e) {
                console.error(e);
            }

            map = this.map;
            this_extent = this.extent;

            //overload the zoomToMaxExtent function of Openlayers
            if (this.restrictMap)
            {
                map.zoomToMaxExtent = function() {
                    try {
                        var extent = new OBounds(this_extent);
                        if (extent.validRect()) {
                            map.setCenter(extent.getCenterLonLat(),map.getZoomForExtent(extent));
                        } else {
                            map.setCenter((new OpenLayers.LonLat(this.initLng, this.initLat)).transform(map.displayProjection, map.projection ) ,this.initZoomlevel, false, true);
                        }
                    } catch(e) {
                        console.error(e);
                    }
                };
            }


            map.reorder_layers = function() {
                var layers = [];
                var last_baseLayer;
                var i;
                for (i = 0; i < this.layers.length; i++) {
                    if (this.layers[i].isBaseLayer) {
                        last_baseLayer = i;
                    } else {
                        var weight = this.layers[i].lizard_index || 0;
                        layers.push([weight, this.layers[i]]);
                    }
                }
                layers.sort();

                for (i = layers.length-1; i >= 0; i--) {
                    this.setLayerIndex(layers[i][1], last_baseLayer+1);
                }
            };

        } else {
            console.error("kies map engine die ondersteunt wordt");
        }
    }  else {
        console.info("map is al geinitialiseerd");
    }
    this.screen[MAP].init = true;
};

/**
 * function: destroy Openlayers Map for mainscreen
 */
NMainScreenManager.prototype.destroyMap = function() {
    this.map.destroy();
    this.screen[MAP].init = false;
    map = null;
};

/**
 * function:
 */
NMainScreenManager.prototype.setMapDataVisible = function() {

};

/**
 * function:
 */
NMainScreenManager.prototype.setMapDataHidden = function() {

};

//function still worked on


console.log('loaded NMainScreenManager successfully');
