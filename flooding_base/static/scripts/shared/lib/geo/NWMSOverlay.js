console.log('NWMSOverlay laden ...');

/****************************************************************/
/**** class:         NWMSOverlay                                 */
/**** description:     This class represents an overlay that...    */
/**** notes:        This class inherits from NMapOverlay        */
/****************************************************************/

/*
  Subclass of NMapOverlay. Besides the properties already set by
  NMapOverlay's constructor, the following are also set:

  type = WMSOVERLAY instead of MAPOVERLAY
  cloud_settings (from options.cloude, default {})
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
function NWMSOverlay(id, name, options) {
    options = options || {};
    this.__superclass(id,name, options);

    this.type = WMSOVERLAY;

    this.cloud_settings = options.cloud || {};
    this.showLoadingMessage = options.showLoadingMessage || false;
    this.loadingMessageDiv = options.loadingMessageDiv || 'map';

    //options for WMS
    this.singleTile = options.singleTile || false;
    this.maxExtent = options.maxExtent || null;
    if (this.maxExtent) {
        this.displayOutsideMaxExtent = false;
    } else {
        this.displayOutsideMaxExtent = true;
    }

    //options for menu
    this.locationMenuShowIdColumn = options.locationMenuShowIdColumn || true;
    this.locationMenuShowNameColumn = options.locationMenuShowNameColumn || true;
    this.locationMenuWidth = options.locationMenuWidth || 130;
}

// property is called __superclass as this.superclass in the subclass of NWMSOverlay refers to an other instance
NWMSOverlay.prototype = new NMapOverlay();
NWMSOverlay.prototype.superclass = NMapOverlay;
NWMSOverlay.prototype.__superclass = NMapOverlay;


/*** Initializes the NWMSOverlay instance ***/
NWMSOverlay.prototype.init = function(callback) {
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

    if (this.getSettingsFromRequest) {
        this.getLayerSettingsByRequestData(totalCallback);
    } else {
        totalCallback();
    }

    this.cloud = new NCloudManager(this.cloud_settings);
};



/*** Destroys the object, such that it can be removed by the garbage collector ***/
NWMSOverlay.prototype.destroy = function() {
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


/*** Event handler when is clicked on the map ***/
NWMSOverlay.prototype.click = function(evt) {
    if (typeof(evt.target) != 'undefined'){
        if (evt.target.className == "olPopupCloseBox") {
            return false;
        }
    }

    var xy = map.events.getMousePosition(evt);
    xy = map.getLonLatFromViewPortPx(xy);



    var x = evt.clientX;
    var y = evt.clientY;

    var this_ref = this;
    ds_get_node.dataURL = this.frameUrl;

    RPCManager.sendRequest({
        actionURL: this.frameUrl,
        useSimpleHttp: true,
        httpMethod: "GET",
        params: {action: 'get_shapes', result_id: this.id, x:xy.lon, y: xy.lat, precision: (map.getResolution()*10) },
        callback: function(response, data, request){
            if (response.httpResponseCode == 200) {
                data = JSON.parse(data);
                console.log("Data ophalen gelukt, tonen op scherm.");
                var length = data.length * 1;
                console.log('aantal punten: ' + length );
                if (length <= 0) {
                    this_ref.cloud.removePopup();
                    this_ref.removeMenu();
                    console.log('geen punt geselecteerd');
                } else if (length == 1) {
                    this_ref.removeMenu();
                    //to do imlement: params: selectedLocation, id, name, service_url, param
                    this_ref.cloud.refreshContent({id:data[0].id, lon:xy.lon, lat:xy.lat}, data[0].id, data[0].name, this_ref.frameUrl, {sobek_id:data[0].id, result_id:this_ref.id} );
                } else if (length > 1) {
                    var a=x;
                    this_ref.cloud.removePopup();
                    this_ref.setMenu(x, y, data, function(record) {
                        this_ref.removeMenu();
                        //to do imlement: params: selectedLocation, id, name, service_url, params
                        this_ref.cloud.refreshContent({id:record.id, lon:xy.lon, lat:xy.lat}, record.id, record.name, this_ref.frameUrl, {sobek_id:record.id, result_id:this_ref.id} );
                    });
                } else {
                    console.log('dit kan dus niet!');
                    this_ref.cloud.removePopup();
                    this_ref.removeMenu();
                }
            } else {
                console.log("Fout bij het ophalen van gegevens.");
            }
        }
    });

}

/*** Sets and shows the menu in which the user can choose between multiple locations that
     are close to each other, when the user clicks in the area of those locations on the map. ***/
NWMSOverlay.prototype.setMenu = function(x,y,items, funct) {
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
NWMSOverlay.prototype.removeMenu = function(x,y,items, funct) {
    if ((typeof(screenMenu) != 'undefined')) {
        screenMenu.hide();
    }
};


/*** Initializes?? ***/
NWMSOverlay.prototype._init = function() {
    var map_options = {
        singleTile:this.singleTile,
        isBaseLayer: false,
        displayInLayerSwitcher:this.displayInLayerSwitcher,
        units: 'm'
    };

    if (!this.displayOutsideMaxExtent) {
        map_options.maxExtent = this.maxExtent;
        map_options.displayOutsideMaxExtent = this.displayOutsideMaxExtent;
    }

    this.layer = new OpenLayers.Layer.WMS(this.name, this.frameUrl , this.framesRequestParams , map_options);
    map.events.register('click',this,this.click);
    if (this.showLoadingMessage) {
        var this_ref = this;
        var loadingMessageActive = false;
        var container = document.createElement("div");
        container.style.overflow="hidden";
        container.style.position= "absolute";
        container.style.top= 2;
        container.style.left= 50;
        container.style.zIndex = 100000;
        container.style.backgroundColor = 'white';
        container.innerHTML = ST_LOADING_TILES;

        var onTileLoaded = function () {
            if (this.numLoadingTiles > 0 && !loadingMessageActive) {
                document.getElementById(this_ref.loadingMessageDiv).appendChild(container);
                loadingMessageActive = true;
            } else if (this.numLoadingTiles <= 0 && loadingMessageActive){
                document.getElementById(this_ref.loadingMessageDiv).removeChild(container);
                loadingMessageActive = false;
            }
        };
        this.layer.events.register('tileloaded', this.layer, onTileLoaded);
    }
    if (this.visible) {
        this.show();
    }

    this.isInit = true;
};

/*** Redraws the map (can be called for example when new request
     parameters (e.g. legend)) for the map have been set) ***/
NWMSOverlay.prototype.redraw = function(){
    if (this.isInit) {
        this.layer.mergeNewParams({ct:(new Date()).valueOf()});
    }
};


/*** NOTE: Overriding method in NMapOverlay ***/
NWMSOverlay.prototype.preLoad = function() {
    console.log('preload doet niks');
};


/*** NOTE: Overriding method in NMapOverlay ***/
NWMSOverlay.prototype.getUrl = function(frameNr) {
    console.log('getUrl doet niks');
    return 0;
};


/*** NOTE: Overriding method in NMapOverlay ***/
NWMSOverlay.prototype.relocate = function( ) {
    console.log('relocate doet niks');
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
