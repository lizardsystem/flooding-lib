console.log('NMapOverlay laden ...');

/****************************************************************/
/**** class:         NMapOverlay                                 */
/**** description:     This class represents an overlay with ...   */
/**** notes:        This class inherits from NOverlay           */
/****************************************************************/

/*
   Subclass of NOverlay. Besides the properties set in NOverlay's
   constructor, the following are also set:

   type = MAPOVERLAY (defined where?)
   isInit = false

   getSettingsFromPgw (default false)
   getSettingsFromRequest (default false)
   settingsRequestUrl (default null)
   settingsRequestParams (default {})
   framesFromRequest (default false)
   frameUrl (default null)
   framesRequestParams (default {})
   rawResultUrl (default null)
   bounds (default null, can also be retrieved from pgw)
   size (default null, can also be retrieved from pgw)
   pictureSize (OpenLayer.Size, initialized from size if present)

   overlayManager (default null, can also be set when added to manager)
   events = []
   events_active = false
*/

/*
  Defines the following methods:

  NMapOverlay.prototype._init
  NMapOverlay.prototype.activateEvents
  NMapOverlay.prototype.addToMap
  NMapOverlay.prototype.addToOverlayManager
  NMapOverlay.prototype.deactivateEvents
  NMapOverlay.prototype.destroy
  NMapOverlay.prototype.getLayerSettingsByFileData
  NMapOverlay.prototype.getLayerSettingsByRequestData
  NMapOverlay.prototype.getRawResultUrl
  NMapOverlay.prototype.getUrl
  NMapOverlay.prototype.hide
  NMapOverlay.prototype.init
  NMapOverlay.prototype.preLoad
  NMapOverlay.prototype.redraw
  NMapOverlay.prototype.relocate
  NMapOverlay.prototype.resetPreLoad
  NMapOverlay.prototype.setActiveLegend
  NMapOverlay.prototype.setOpacity
  NMapOverlay.prototype.setParams
  NMapOverlay.prototype.show

*/

function NMapOverlay(id,name,options) {
    options = options || {};
    this._superclass(id, name, options);

    this.type = MAPOVERLAY;
    this.isInit = false;

    this.getSettingsFromPgw = options.getSettingsFromPgw || false;
    this.getSettingsFromRequest = options.getSettingsFromRequest || false;
    this.settingsRequestUrl = options.settingsRequestUrl || null;
    this.settingsRequestParams = options.settingsRequestParams || {};

    this.framesFromRequest = options.getFramesFromRequest || false;
    this.frameUrl = options.frameUrl || null;
    this.framesRequestParams = options.framesRequestParams || {};
    this.rawResultUrl = options.rawResultUrl || null;

    //settings which can also be get from pgw // request
    this.bounds = options.bounds || null;
    this.size = options.size || null;
    if (this.size) {
        this.pictureSize = new OpenLayers.Size(this.size.width, this.size.height);
    }

    //settings which can are also set when added2 overlayManager
    this.overlayManager = options.overlayManager || null;
    this.events = [];
    this.events_active = false;
}

// _superclass is used for solving inheritance problems (this.superclass is also defined in the child)
NMapOverlay.prototype = new NOverlay();
NMapOverlay.prototype.superclass = NOverlay;
NMapOverlay.prototype._superclass = NOverlay;

/*** Initialize the NMapOverlay. The parameter 'callback' is a method that will be exectued after
     the settings for the layer have been retrieved. If there are no settings for the layer, the
     method will also be executed. ***/
NMapOverlay.prototype.init = function(callback) {
    if (this.isInit) {
        return;
    }

    callback = callback || function() {};
    var layer_ref = this;

    var totalCallback = function() {
        console.log('execute totalcallback');
        layer_ref._init();
        callback();
    };

    if (this.getSettingsFromPgw) {
        this.getLayerSettingsByFileData(totalCallback);
    } else if (this.getSettingsFromRequest) {
        this.getLayerSettingsByRequestData(totalCallback);
    } else {
        totalCallback();
    }
    if (this.visible) {
        this.show();
    }
};


NMapOverlay.prototype._init = function() {
    console.log('init mapoverlay');
    this.Obounds = new OBounds(this.bounds, this._map.getExtent());

    this.layer = new OpenLayers.Layer.Image(this.name, this.getUrl(), this.Obounds, this.pictureSize,{
        isBaseLayer: false,displayInLayerSwitcher: this.displayInLayerSwitcher, //reproject: true,
        maxResolution: 100000, minResolution: 0.000001
    });
    this.events.push({moment:"moveend", action:this.relocate });

    this.isInit = true;
};


NMapOverlay.prototype.preLoad = function() {
    (new Image()).src = this.getUrl() ;
};


/*** Empty function: overide in case of animated ()MapOverlay) ***/
NMapOverlay.prototype.resetPreLoad = function() {
};


NMapOverlay.prototype.addToOverlayManager = function(overlayManager, callback) {
    this.overlayManager = overlayManager;
    this._map = this.overlayManager._map;
    this.init(callback);
};


NMapOverlay.prototype.addToMap = function(map, callback) {
    this._map = map;
    this.init(callback);
};


/*** Creates and returns the url where the overlay image can be found ***/
NMapOverlay.prototype.getUrl = function(frameNr) {
    var url;
    if (this.framesFromRequest) {
        if (frameNr !== null) {
            this.framesRequestParams.framenr = frameNr;
        }
        url = this.frameUrl + '?';
        var first = true;
        for (var elem in this.framesRequestParams) {
            if (!first) { url+='&'; } else { first = false; }
            url += elem + '=' + this.framesRequestParams[elem];
        }
        if (typeof dynamic_legend.maxvalue !== "undefined") {
            if (!first) { url+='&'; } else { first = false; }
            url += "maxvalue=" + dynamic_legend.maxvalue;
        }
        if (typeof dynamic_legend.colormap !== "undefined") {
            if (!first) { url+='&'; } else { first = false; }
            url += "colormap=" + dynamic_legend.colormap;
        }
        return url;
    } else {
        if (frameNr !== null) {

            var loc = this.frameUrl;
            url = loc.replace(/#+/ , function(word) {
                var result;
                if (frameNr.toFixed) {
                    result = frameNr.toFixed(); //round value
                } else {
                    result = frameNr.toString();
                }
                for (var j = result.length ; j < word.length; j++) {
                    result = "0" + result;
                }
                return result;
            });

            return url;

        } else {
            return this.frameUrl;
        }
    }
};


NMapOverlay.prototype.relocate = function( ) {

    this.Obounds = new OBounds(this.bounds, this._map.getExtent());

    this.layer.bounds = this.Obounds;
    this.layer.extent = this.Obounds;
    this.layer.redraw();

    console.log("layer "+ this.name +" moved " + this.Obounds.left + " " + this.Obounds.right +" " + this.Obounds.bottom );
};


NMapOverlay.prototype.activateEvents = function() {
    if (!this.events_active) {
        for (var i = 0 ; i < this.events.length ; i++) {
            ev = this.events[i];
            console.log('register event '+ ev.action + ' on moment '+ ev.moment);
            this._map.events.register(ev.moment, this, ev.action);
        }
        this.events_active = true;
    }
};


NMapOverlay.prototype.deactivateEvents = function() {
    if (this.events_active) {
        for (var i = 0 ; i < this.events.length ; i++) {
            ev = this.events[i];
            console.log('unregister event '+ ev.action + ' on moment '+ ev.moment);
            this._map.events.unregister(ev.moment, this, ev.action);
        }
        this.events_active = false;
    }
};


NMapOverlay.prototype.show = function(timestep, opacity) {
    console.log("In NMapOverlay.show, opacity is "+opacity);
    if (opacity == null) { opacity = 1; }
    if (this.layer) {
        try {
            if (this.overlayManager !== null) {
                console.log("Setting opacity by overlayManager, " +
                            this.overlayManager.opacity);
                this.layer.setOpacity( this.overlayManager.opacity );
            } else {
                console.log("Setting opacity "+ opacity);
                this.layer.setOpacity( opacity );
            }

            this.layer.lizard_index = this.layerIndex;
            this._map.addLayer(this.layer);
            this._map.reorder_layers();

            if (timestep !== null) {
                this.setParams({timestep:timestep});
            }
            this.activateEvents();

            this.showLegendSection();
        } catch (e){
            console.log(e);
        }
    }
};


NMapOverlay.prototype.hide = function() {
    if (this.layer) {
        try {
            this.deactivateEvents();
        } catch (e){
            console.log(e);
        }
        try {
            this._map.removeLayer(this.layer);
            this.hideLegendSection();
        } catch (e){
            console.log(e);
        }
    }
};


/*** Redraws the laye ***/
NMapOverlay.prototype.redraw = function( ) {
    if (this.isInit) {
        this.layer.setUrl(this.getUrl());
    }
};


NMapOverlay.prototype.destroy = function() {
    this.hide();
    try {
        this.layer.destroy();
    } catch (e) {
        console.log(e);
    }
};


NMapOverlay.prototype.setOpacity = function(opacity){
    if (this.layer) {
        this.layer.setOpacity(opacity);
    }
};


NMapOverlay.prototype.setParams= function(params){
    for (var elem in params) {
        this.framesRequestParams[elem] = params[elem];
    }
    if (this.isInit) {
        if (typeof(this.layer.mergeNewParams) != 'undefined') {
            this.layer.mergeNewParams(params);
        } else {
            this.resetPreLoad();
            this.redraw();
        }
    }
};


/*** Sets the legend of the overlay  ***/
NMapOverlay.prototype.setActiveLegend = function(legend){
    this.setParams({ legend_id: legend.id });
};


NMapOverlay.prototype.getRawResultUrl= function(){
    return this.rawResultUrl;
};


NMapOverlay.prototype.getLayerSettingsByFileData = function(callback){
    var imgnr = 0;
    //var layer_ref = this;
    //internal function. get information after loading figure and download pgw to get extends

    var downloadpgw = function(layer) {
        var nwidth = this.width;
        var nheight = this.height;

        var pgw = new String(this.imgurl);
        pgw = pgw.replace(".png" , ".pgw" );

        RPCManager.sendRequest({
            actionURL: lizardKbFloodPngDirectory + pgw,
            callback: function(response, data, request){
                console.log(request);
                console.log(response);
                if (response.httpResponseCode == 200) {
                    var info = JSON.parse(data);

                    layer.gridsize = info.rec.gridsize;
                    layer.bounds = {};
                    layer.bounds.west = info.rec.west; // - 0.5*gridsize;
                    layer.bounds.north = info.rec.north; // + 0.5*gridsize;
                    layer.bounds.east = info.rec.east + (nwidth) * layer.gridsize;
                    layer.bounds.south = info.rec.south - (nheight) * layer.gridsize;
                    layer.bounds.projection = info.rec.projection || 'rds';
                    layer.pictureSize = new OpenLayers.Size(nwidth, nheight);


                }
                else {
                    console.log("error in het ophalen van gegevens ");
                    alert('kan gegevens niet van server halen.');
                }
                if (callback) {
                    callback(layer_ref);
                }
            }
        });
    }

    //internal function. get figure and start downloading pgw
    downloadFigure = function(layer,  imgurl) {
        //get bounds from pgw file (a-synchroom)
        img[imgnr] = {};
        img[imgnr].img  = new Image();

        img[imgnr].img.onload = downloadpgw;

        //item.last_selected =  last_selected;
        //img[imgnr].img.pass2load = layer;

        img[imgnr].img.onerror = function(layer) {
            console.log("error loading png");
            alert('kan figuren niet van server halen');
        };
        //load picture and start a-synchroon actions to add overlay
        img[imgnr].img.imgurl = imgurl;
        img[imgnr].img.src = imgurl;
        imgnr++;
    };
    //create new overlays
    var img = {};

    var imgurl =  new String( overlay.frameUrl);
    if (this.type == 'MAPOVERLAY') {
        downloadFigure(this,imgurl);
    } else if (this.type == 'ANIMATEDMAPOVERLAY') {
        //make file name of first picture
        imgurl = imgurl.replace(/#+/ , function(word){
            var result;
            if (this.animation.firstnr.toFixed) {
                result = "" + this.animation.firstnr.toFixed(); //round value
            }
            else {
                result = this.animation.firstnr.toString();
            }
            for (var j = result.length; j < word.length; j++) {
                result = "0" + result;
            }
            return result;
        });
        downloadFigure(this,imgurl);
    } else {
        console.log("overlay type wordt nog niet ondersteund");
    }
};


/*** Request the settings from an URL. The callback parameter is a method that will
     be executed after all settings are retrieved from the URL.                     ***/
NMapOverlay.prototype.getLayerSettingsByRequestData = function(callback){
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

                console.log(data);
                data = JSON.parse(data);

                if (layer_ref.geoType == 1) {
                    layer_ref.bounds = data.rec.bounds; //new OBounds(data);
                    layer_ref.pictureSize = new OpenLayers.Size(data.rec.width, data.rec.height);
                }
                if (layer_ref.valueType == 3) {
                    if (layer_ref.animation === null) {
                        layer_ref.animation = new NAnimation(data.anim.firstnr, data.anim.lastnr, data.anim.options);
                    } else {
                        layer_ref.animation.updateSettings(data.anim.firstnr, data.anim.lastnr, data.anim.options);
                    }
                }
                if (data.legends) {
                    console.log('requested available legend = ' + data.legends);
                    console.log('requested default legend = ' + data.default_legend);
                    layer_ref.setAvailableLegends(data.legends);
                    layer_ref.setDefaultLegend(data.default_legend);
                } else {
                    console.log("No data.legends");
                }
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


//extra function for showing and hiding overlay. To get a smooth animation and
//no problems with memory usage (internet explorer), the strategy is different for different browsers
OpenLayers.Layer.Image.prototype.hide = function (realhide){
    realhide = realhide || false;

    //if (isc.Browser.isIE || realhide) {
    //    this.setVisibility( false );
    //} else {
        this.setOpacity( 0 );
    //}
};


OpenLayers.Layer.Image.prototype.show = function (opacity){
    opacity = opacity || 1;
    this.setOpacity( opacity );
    //if (isc.Browser.isIE || !this.getVisibility()) {
    //    this.setVisibility( true );
    //}
};


console.log('NMapOverlay geladen ...');
