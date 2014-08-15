console.log('NAnimatedMapOverlay laden ...');

/****************************************************************/
/**** class:         NAnimatedMapOverlay                         */
/**** description:     This class represents an overlay with       */
/****               animated maps                                */
/**** notes:        This class inherits from NMapOverlay        */
/****************************************************************/


//options: legenda,
function NAnimatedMapOverlay(id,name,options) {
    options = options || {};
    this.superclass(id,name, options);
    this.isInit = false;

    this.type = ANIMATEDMAPOVERLAY;

    this.nrPreLoadFrames = options.nrPreLoadFrames || 10;
    this.nrPreAddToMap = options.nrPreAddToMap || 3; // not yet supported
    this.removeDelay = options.removeDelay || 150;
    this.currentFrame = -1;
    this.animation = options.animation || null;
    this.events = [];
}

NAnimatedMapOverlay.prototype = new NMapOverlay();
NAnimatedMapOverlay.prototype.superclass = NMapOverlay;

NAnimatedMapOverlay.prototype._init = function() {

    //TO DO: load data

    this.frame = new Array(this.animation.lastnr);
    //alert(bounds);

    for (var i = 0 ; i < this.animation.lastnr ; i++) {
        this.frame[i] = {};
        //this.frame[i].url = this.getUrl(i);
        this.frame[i].npreLoaded = false;
    }

    this.activeFrame = null;
    this.activeLayer = 0;


    this.Obounds = new OBounds(this.bounds, this.overlayManager._map.getExtent());

    this.layer = [];
    for (i = 0; i < this.nrPreAddToMap ; i ++ ) {
        this.layer[i] = new OpenLayers.Layer.Image(this.name+i , this.getUrl(0), this.Obounds, this.pictureSize, {
            isBaseLayer: false,displayInLayerSwitcher:this.displayInLayerSwitcher,//reproject: true,
            maxResolution: 100000, minResolution: 0.000001
        });
        this.layer[i].lizard_index = this.layerIndex;

        this.layer[i].loadedFrame = -1;
        this.overlayManager._map.addLayer(this.layer[i]);
        this.layer[i].hide();

    }
    this.overlayManager._map.reorder_layers();
    this.events.push({moment:"moveend", action:this.relocate });
    this.isInit = true;
};


NAnimatedMapOverlay.prototype.relocate = function( ) {
    this.Obounds = new OBounds(this.bounds, this.overlayManager._map.getExtent());

    for (var i = 0; i < this.nrPreAddToMap; i++) {
        this.layer[i].bounds = this.Obounds;
        this.layer[i].extent = this.Obounds;
        this.layer[i].redraw();
    }
    console.log("layer "+ this.name +" moved " + this.Obounds.left + " " + this.Obounds.right +" " + this.Obounds.bottom );
};

NAnimatedMapOverlay.prototype.resetPreLoad = function() {
    for (var i = 0 ; i < this.frame.length ; i++) {
        this.frame[i].npreLoaded = false;
    }
    for (i = 0; i < this.nrPreAddToMap; i++)  {
        this.layer[i].loadedFrame = -1;
    }
};

NAnimatedMapOverlay.prototype.preLoad = function(currentFrame) {
    currentFrame = currentFrame || 0;

    for (var i = currentFrame+1 ;  i < Math.min((currentFrame + this.nrPreLoadFrames), this.frame.length); i++) {
        if (!this.frame[i].npreLoaded) {
            (new Image()).src = this.getUrl(i);
            this.frame[i].npreLoaded = true;
        }
    }
    //make preload positions free
    for (i = 0; i < this.nrPreAddToMap; i++) {
        if (this.layer[i].loadedFrame < currentFrame) {
            this.layer[i].loadedFrame = -1;
        }
        if (this.layer[i].loadedFrame > currentFrame + this.nrPreAddToMap) {
            this.layer[i].loadedFrame = -1;
        }
    }

    //fill preload positions
    for (var ii = currentFrame+1 ;  ii < Math.min((currentFrame + this.nrPreAddToMap), this.frame.length); ii++) {
        var present = false;
        for (i = 0; i < this.nrPreAddToMap; i++) {
            if (this.layer[i].loadedFrame == ii ) {
                present = true;
            }
        }
        if (!present) {
            for (i = 0; i < this.nrPreAddToMap; i++) {
                if (this.layer[i].loadedFrame == -1 ) {
                    //add2map!
                    this.layer[i].setUrl(this.getUrl(ii));
                    this.layer[i].loadedFrame = ii;
                    break;
                }
            }
        }
    }
};

NAnimatedMapOverlay.prototype.destroy = function() {
    this.hideLegendSection();
    this.deactivateEvents();

    for (var i = 0; i < this.nrPreAddToMap; i++) {
        try {
            this.overlayManager._map.removeLayer(this.layer[i]);
            this.layer[i].destroy();
            this.layer[i] = null;
        } catch (e) {console.log("gedurende destroy() " + e );}
    }
    //delete this.layer;
    this.imgPreload = null;
};

NAnimatedMapOverlay.prototype.show = function(frameNr) {
    this.currentFrame = frameNr;
    var present = -1;
    for (var i = 0; i < this.nrPreAddToMap; i++) {
        if (this.layer[i].loadedFrame == frameNr ) {
            present = i;
        }
    }
    if (present < 0) {
        //add to map
        console.log("frame niet gepreload, alsnog toegevoegd. frame nr " + frameNr);
        present = 0;
        this.layer[0].setUrl(this.getUrl(frameNr));
        this.layer[0].loadedFrame = frameNr;
    }
    console.log("preload positie " + present);
    this.layer[present].show( this.overlayManager.opacity );
    this.activeFrame = this.frame[frameNr];
    this.activeLayer = present;

    //hide other frames
    for (i = 0; i < this.nrPreAddToMap; i++) {
        if (i != present) {
            this.layer[i].hide();
        }
    }

    this.activateEvents();

    this.preLoad(frameNr);
    this.showLegendSection();
};

NMapOverlay.prototype.redraw= function(){
    if (this.isInit) {
        this.show(this.currentFrame);
    }
};

NAnimatedMapOverlay.prototype.hide = function(){

    if (this.activeFrame !== null) {
        try {
            this.deactivateEvents();
            this.layer[this.activeLayer].hide();
            this.hideLegendSection();
        } catch (e){
            console.log(e.Exception);
        }
        this.activeFrame = null;
    }
};

NAnimatedMapOverlay.prototype.setOpacity = function(opacity){
    if (this.layer) {
        this.layer[this.activeLayer].setOpacity(opacity);
    }
};

NAnimatedMapOverlay.prototype.hover_handler = function (lon, lat, callback) {
    // See if there is hover handler for this overlay.

    RPCManager.sendRequest({
        actionURL: '/flooding/tools/pyramids/animation_value',
        useSimpleHttp: true,
        httpMethod: "GET",
        params: {
            'presentationlayer_id': this.id,
            'framenr': this.currentFrame || 0,
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




console.log('NAnimatedMapOverlay geladen ...');