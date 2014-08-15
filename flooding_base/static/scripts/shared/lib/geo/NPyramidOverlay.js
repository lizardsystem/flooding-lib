console.log('NPyramidOverlay laden ...');

/****************************************************************/
/**** class:         NPyramidOverlay                                 */
/**** description:     This class represents an overlay that...    */
/**** notes:        This class inherits from NMapOverlay        */
/****************************************************************/


/*
  Subclass of NMapOverlay. Besides the properties already set by
  NMapOverlay's constructor, the following are also set:

  type = PYRAMIDOVERLAY instead of MAPOVERLAY

  showLoadingMessage (default {})
  loadingMessageDiv (default {})

  singleTile (default false)
  maxExtent (default null)
  displayOutsideMaxExtent (true iff maxExtent present)

  locationMenuShowIdColumn (default true)
  locationMenuShowNameColumn (default true)
  locationMenuWidth (default 130)
*/

/*
  Defines the following methods:

  NWMSOverlay.prototype._init (overrides NMapOverlay)
  NWMSOverlay.prototype.click
  NWMSOverlay.prototype.destroy (overrides NMapOverlay)
  NWMSOverlay.prototype.getUrl (overrides NMapOverlay)
  NWMSOverlay.prototype.init (overrides NMapOverlay)
  NWMSOverlay.prototype.preLoad (overrides NMapOverlay)
  NWMSOverlay.prototype.redraw (overrides NMapOverlay)
  NWMSOverlay.prototype.relocate (overrides NMapOverlay)
  NWMSOverlay.prototype.removeMenu
  NWMSOverlay.prototype.setMenu

*/

/****************** NWMS Overlay ****************/
function NPyramidOverlay(id, name, options) {
    console.log("NPyramidOverlay constructor, options:");
    console.log(options);
    options = options || {};
    this.__superclass(id,name, options);

    this.type = PYRAMIDOVERLAY;
    this.isInit = false;
    this.id = id;
    this.name = name;

    this.getSettingsFromPgw = false;
    this.getSettingsFromRequest = true;
    this.settingsRequestUrl = flooding_config.pyramid_parameters_url;
    this.settingsRequestParams = {
        presentationlayer_id: id      // presentationlayer_id
    };

    this.framesFromRequest = true;
    this.frameUrl = options.frameUrl || null;

    this.rawResultUrl = null;

    this.cloud_settings = {};
    this.showLoadingMessage = options.showLoadingMessage || false;
    this.loadingMessageDiv = options.loadingMessageDiv || 'map';

    //settings which can are also set when added2 overlayManager
    this.overlayManager = options.overlayManager || null;

    //options for WMS
    this.singleTile = true;
    this.maxExtent = options.maxExtent || null;
    if (this.maxExtent) {
        this.displayOutsideMaxExtent = false;
    } else {
        this.displayOutsideMaxExtent = true;
    }
    this.events = [];

    //options for menu
    this.locationMenuShowIdColumn = options.locationMenuShowIdColumn || true;
    this.locationMenuShowNameColumn = options.locationMenuShowNameColumn || true;
    this.locationMenuWidth = options.locationMenuWidth || 130;

    //init
}

// property is called __superclass as this.superclass in the subclass of NPyramidOverlay refers to an other instance
NPyramidOverlay.prototype = new NMapOverlay();
NPyramidOverlay.prototype.superclass = NMapOverlay;
NPyramidOverlay.prototype.__superclass = NMapOverlay;


/*** Initializes the NPyramidOverlay instance ***/
NPyramidOverlay.prototype.init = function(callback) {
    if (this.isInit) {
        this.show();
        return;
    }

    callback = callback || function() {};
    var layer_ref = this;

    var totalCallback = function() {
        layer_ref._init();
        callback();
    };

    this.getLayerSettingsByRequestData(totalCallback);

    this.cloud = new NCloudManager(this.cloud_settings);
};


NPyramidOverlay.prototype.getLayerSettingsByRequestData = function(callback){
    console.log("getLayerSettingsByRequestData");
    console.log("url "+this.settingsRequestUrl);
    console.log("params"+this.settingsRequestParams);

    var layer_ref = this;
    var postParams = this.settingsRequestParams;

    RPCManager.sendRequest({
        actionURL: this.settingsRequestUrl,
        showPrompt:true,
        useSimpleHttp: true,
        httpMethod: "GET",
        params: postParams,
        callback: function(response, data, request){
            if (response.httpResponseCode == 200) {
                console.log("Data ophalen gelukt.");

                data = JSON.parse(data);
                console.log(data);

                layer_ref.layer_id = data.layer;
                layer_ref.default_colormap = data.default_colormap;
                layer_ref.default_maxvalue = data.default_maxvalue;

                // hrm
                layer_ref.setAvailableLegends([{"id": layer_ref.id, "name": "Dummy name"}]);
                layer_ref.setDefaultLegend({"id": layer_ref.id, "name": "Dummy name"});

                //if a callback function is specified, execute this function
                if (callback) {
                    console.log('callback after getting request data');
                    callback();
                }
            } else {
                console.log("Fout bij het ophalen van gegevens.");
            }
        }
    });
};


/*** Destroys the object, such that it can be removed by the garbage collector ***/
NPyramidOverlay.prototype.destroy = function() {
    map.events.unregister('click',this,this.click);
    if (this.cloud) {
        this.cloud.destroy();
    }

    try {
        this.overlayManager._map.removeLayer(this.layer);
        this.hideLegendSection();
    } catch (e){
        console.log(e);
    }
    try {
        this.layer.destroy();
    } catch (e){
        console.log(e);
    }
};


/*** Sets and shows the menu in which the user can choose between multiple locations that
     are close to each other, when the user clicks in the area of those locations on the map. ***/
NPyramidOverlay.prototype.setMenu = function(x,y,items, funct) {
    //screenMenu.hide();
    this.menu = {};
    this.menu.funct = funct || function() {};

    var this_ref = this;

    var fieldlist = [];
    if (this_ref.locationMenuShowIdColumn)
    {
        fieldlist.push({name: "id", title: "id", type: "text", hidden:true, width:40});
    }
    if (this_ref.locationMenuShowNameColumn)
    {
        fieldlist.push({name: "name", title: "locatie", type: "text"});
    }

    // Create the menu if it is does not exist
    if (typeof(screenMenu) == 'undefined') {
        isc.ListGrid.create({
            ID: "screenMenu",
            width: this_ref.locationMenuWidth,
            fields: fieldlist
        });
    }

    screenMenu.recordClick = function(viewer,item,recordNum) {
        screenMenu.hide();
        this_ref.menu.funct(item);
    };
    screenMenu.moveTo(x,y);
    screenMenu.setData(items);
    screenMenu.show();
};

/*** Removes the menu in which the user can choose between nearby locations. ***/
NPyramidOverlay.prototype.removeMenu = function(x,y,items, funct) {
    if ((typeof(screenMenu) != 'undefined')) {
        screenMenu.hide();
    }
};

/*** Initializes ***/
NPyramidOverlay.prototype._init = function() {
    var map_options = {
        singleTile: true,
        isBaseLayer: false,
        displayInLayerSwitcher: this.displayInLayerSwitcher,
        units: 'm'
    };

    if (!this.displayOutsideMaxExtent) {
        map_options.maxExtent = this.maxExtent;
        map_options.displayOutsideMaxExtent = this.displayOutsideMaxExtent;
    }

    this.layer = new OpenLayers.Layer.WMS(
        "pyramid",
        flooding_config.raster_server_url , {
        'layers': this.layer_id,
        'styles': this.getStyleParam()
    } , map_options);

    this.show();

    this.isInit = true;
};

NPyramidOverlay.prototype.getStyleParam = function () {
    var colormap = dynamic_legend.colormap || this.default_colormap;
    var maxvalue = dynamic_legend.maxvalue || this.default_maxvalue;
    return colormap + ":0:" + maxvalue;
};

/*** Redraws the map (can be called for example when new request
     parameters (e.g. legend)) for the map have been set) ***/
NPyramidOverlay.prototype.redraw = function(){
    if (this.isInit) {
        this.layer.mergeNewParams({styles: this.getStyleParam()});
    }
};


/*** NOTE: Overriding method in NMapOverlay ***/
NPyramidOverlay.prototype.preLoad = function() {
    console.log('preload doet niks');
};


/*** NOTE: Overriding method in NMapOverlay ***/
NPyramidOverlay.prototype.getUrl = function(frameNr) {
    console.log('getUrl doet niks');
    return 0;
};


/*** NOTE: Overriding method in NMapOverlay ***/
NPyramidOverlay.prototype.relocate = function( ) {
    console.log('relocate doet niks');
};


NPyramidOverlay.prototype.hover_handler = function (lon, lat, callback) {
    RPCManager.sendRequest({
        actionURL: '/flooding/tools/pyramids/pyramid_value',
        useSimpleHttp: true,
        httpMethod: "GET",
        params: {
            'presentationlayer_id': this.id,
            'lat': lat,
            'lon': lon
        },
        callback: function(response, data, request) {
            data = JSON.parse(data);
	    
            if (typeof data.value !== "undefined") {
                callback(data.value.toFixed(2) + " " + data.unit);
            }
        }
    });
};


/*** NOTE: hide function is an extension for Openlayers! ***/
OpenLayers.Layer.WMS.prototype.hide = function (){
    if (isc.Browser.isIE) {
        this.setVisibility( false );
    } else {
        this.setOpacity( 0 );
    }
};


/*** NOTE: show function is an extension for Openlayers! ***/
OpenLayers.Layer.WMS.prototype.show = function (opacity){
    opacity = opacity || 1;
    this.setOpacity( opacity );
    if (isc.Browser.isIE) {
        this.setVisibility( true);
    }
};
