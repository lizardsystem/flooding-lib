console.log('loading overlaymanager ...');

var MAPOVERLAY= 1;
var ANIMATEDMAPOVERLAY = 2;
var MARKEROVERLAY = 3;
var ANIMATEDMARKEROVERLAY = 4;
var VECTOROVERLAY = 5;
var WMSOVERLAY = 6;
var ANIMATEDWMSOVERLAY = 7;
var PYRAMIDOVERLAY = 8;
var ANIMATEDPYRAMIDOVERLAY = 9;

/******************Overlay Manager***********************/
//options: use overlay select, png prefix, maxFramesPreLoad
var NOverlayManager = function(_map,options) {
    options = options || {};
    this._map = _map;

    this.animationControl = new NAnimationControl(_map,this, null);

    this.overlay = {};
    this.activeOverlay = null;

    this.prefixPngLocation = options.prefixPngLocation || "";
    this.maxFramesPreLoad = options.maxFramesPreLoad || 60;
    this.opacity = 0.7;
};

NOverlayManager.prototype.setMap = function(_map) {
    this._map = _map;
};


/*** Sets the opacity of the layer. The parameter 'opacity' is a float between 0 and 1 ***/
NOverlayManager.prototype.setOpacity = function(opacity) {
    this.opacity = opacity;
    if (this.activeOverlay) {
        this.activeOverlay.setOpacity(opacity);
    }
};


//ok, if statements are ok
NOverlayManager.prototype.destroy = function() {
    this.clearAllOverlays();
    if (this.useOverlaySelect) {this.overlaySelect.remove();}
    this.animationControl.remove();
    for (var el in this) {
        delete this[el];
    }
};

/*** Returns the RawResultUrl of the activer layer  ***/
NOverlayManager.prototype.getRawResultUrl = function() {
    if (this.activeOverlay !== null) {
        return this.activeOverlay.getRawResultUrl();
    } else {
        return null;
    }
};


NOverlayManager.prototype.hide = function() {
    //hide controls
    this.animationControl.hide();
    //hide overlay
    if (this.activeOverlay) {
        this.activeOverlay.hide(true);
    }
};


//TO DO, deze functie herschrijven
NOverlayManager.prototype.show = function() {
    //if animation, show animation control
    if (this.activeOverlay) {
        if (is_animated_overlay(this.activeOverlay)) {
            this.animationControl.show();
            this.showOverlay(this.animationControl.frameNr);
        } else {
            this.showOverlay();
        }
    }
};


/*** Adds an overlay and then initializes the overlay. The paramater 'callbackl' is a method the will be passed
     to the init method. ***/
NOverlayManager.prototype.addOverlay = function(overlay,callback){
    callback = callback || function() {};

    if (this.overlay[overlay.id]) {
        console.log("overlay "+ overlay.id+ "already exist" );
    } else {
        this.overlay[overlay.id] = overlay;
        overlay.addOverlayToOverlaymanager(this);
    }

    overlay.init(callback);
};


NOverlayManager.prototype.addAndSetActiveOverlay = function(overlay) {
    this.hideOverlay();
    this.animationControl.stop();

    if (overlay !== null) {
        //add overlay
        var this_ref = this;
        //a-synchrone
        this.addOverlay(overlay,function(){
            this_ref.setActiveOverlay(overlay.id);
        });
        return true;
    } else {
        console.log("error overlay is null" );
        return false;
    }
};


NOverlayManager.prototype.setActiveOverlay = function(id) {
    //kijk of overlay bestaat
    //to do: 0 verder en logisch invullen
    this.hideOverlay();
    this.animationControl.stop();

    if (this.overlay[id]) {
        this.activeOverlay = this.overlay[id];
        console.log("set overlay to "+ id );
    } else if (id === 0) {
        this.animationControl.hide();
        return true;
    } else {
        console.log("cannot set overlay to "+ id );
        return false;
    }

    //kijk of AnimationControl moet worden toegevoegd
    if (is_animated_overlay(this.activeOverlay)) {
        this.animationControl.show();
        this.animationControl.initOverlay(this.activeOverlay);
        this.animationControl.startFrame();
        if (this.activeOverlay.animation.autoplay) {
            this.animationControl.play();
        }
    } else {
        this.animationControl.hide();
        this.showOverlay();
    }
    //laat legenda zien
    // OUDE CODE???
    if (this.activeOverlay.legenda) {
        var tmp = ( this.activeOverlay.filename).replace('\\','/');
        var reg = /\S*\//;
        var legendaUrl = tmp.match(reg) + 'colormapping.csv';
        this.activeOverlay.legenda.fetchData( legendaUrl, function(legenda,data,responce){
            tabLegenda.setContents(legenda.getHTML());//
            //scLegenda.contents
        });
    }
    return true;
};


NOverlayManager.prototype.addOverlay = function( overlay, callback ) {
    if (this.overlay[overlay.id]) {
        console.log("overlay "+ overlay.id+ "already exist" );
    } else {
        this.overlay[overlay.id] = overlay;
        overlay.addToOverlayManager(this, callback);
    }
};


NOverlayManager.prototype.removeOverlay = function(overlay ) {
    if (this.useoverlaySelect) { this.overlaySelect.removeOption(overlay.id,overlay.name);}
    //this.overlay[overlay.id] = null;
    this.overlay[overlay.id].destroy();
    delete this.overlay[overlay.id] ;
};


NOverlayManager.prototype.clearAllOverlays = function( ) {
    //remember last state
    if (this.activeOverlay) {
        this._lastActive = this.activeOverlay.name;
    }

    for (var elem in this.overlay) {
        this.overlay[elem].destroy();
        delete  this.overlay[elem] ;
    }

    this.activeOverlay = null;
};


NOverlayManager.prototype.hideOverlay = function(realhide) {
    this.animationControl.stop();
    if (this.activeOverlay === null) {
        return false;
    }

    this.activeOverlay.hide(realhide);
    return true;
};


NOverlayManager.prototype.showOverlay = function (frameNr) {
    if (this.activeOverlay === null) {return false;}

    this.activeOverlay.show(frameNr);
    return true;
};


var is_animated_overlay = function(overlay) {
    return (overlay.type == ANIMATEDMAPOVERLAY ||
            overlay.type == ANIMATEDWMSOVERLAY ||
            overlay.type == ANIMATEDPYRAMIDOVERLAY);
};
