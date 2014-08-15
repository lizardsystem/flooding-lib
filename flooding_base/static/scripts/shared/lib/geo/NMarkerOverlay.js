console.log('NMarkerOverlay laden ...');

/********************************************************************/
/**** class: 		NMarkerOverlay         							*/
/**** description: 	This class represents an overlay that       	*/
/****               consists of markers (like icons for bridges,	*/ 
/****               dikes, etc.)									*/
/**** notes:        This class inherits from NOverlay           	*/ 
/********************************************************************/


function NMarkerOverlay(id,name,_map,data,options) {
    var options = options || {};
	
	this.superclass(id,name,options);

    this.type = MARKEROVERLAY;
    this._map = _map;
    this.data = data || new Array();;

    this.canSelect = options.canSelect || false;
    this.canUnselect = options.canUnselect || false;
    this.multipleSelect = options.multipleSelect || false;
    this.clickMarker = options.clickMarker || null;
    this.legend = options.legend || null; //TO DO:default
    this.legendField = options.legendField || null;
    this.zoomLegend = options.zoomLegend || null; //TO DO: deze ondersteunen
    this.zoomLegendField = options.zoomLegendField || null; //TO DO: deze ondersteunen
	this.displayInLayerSwitcher  = options.displayInLayerSwitcher || false;
	
	this.onMouseOver = options.onMouseOver || false;
	this.onMouseOut = options.onMouseOut || false;
    this.isDataTreeFormat = options.isDataTreeFormat || false;
    this.labelIsPoint = options.labelIsPoint || null;
    this.idfield = options.idfield || "id";
    this.latfield = options.latfield || "lat";
    this.lonfield =options.lonfield || "lon";
    this.filter = null;

    this.defaultMarker= options.defaultMarker || new OpenLayers.Icon( "../images/icons/LizardIconRWZIZW.gif",new OpenLayers.Size(16,16),new OpenLayers.Pixel(-8, -8)),
    this.defaultSelectedMarker= options.defaultSelectedMarker || new OpenLayers.Icon( "../images/icons/LizardIconCircleYellow.gif",new OpenLayers.Size(16,16),new OpenLayers.Pixel(-8, -8)),

    //init
    this.frame = new OpenLayers.Layer.Markers(name, {displayInLayerSwitcher: this.displayInLayerSwitcher});
    this.marker = new Array();
    this.isLayerAddedToMap = false;
    this.isPreLoaded = false;

    this.selectedFrame = null;
    this.selectedMarker = null;
    this.isSelectedLayerAddedToMap = false;

    if (this.canSelect) {
        this.selectedFrame = new OpenLayers.Layer.Markers("Geselecteerde " + name, {displayInLayerSwitcher: this.displayInLayerSwitcher});
        this.selectedMarker = new Array();
        this.isSelectedLayerAddedToMap = false;
    }

}

NMarkerOverlay.prototype = new NOverlay();
NMarkerOverlay.prototype.superclass = NOverlay;


NMarkerOverlay.prototype._createMarker = function(i,loc){
    
    var ref_this = this;
    try {
        //MARKER SELECTEREN OP BASIS VAN LOC GEGEVEN
        if (this.legend) {
            var icon = this.legend.getIcon(loc[this.legendField],false);
        } else {
            var icon = this.defaultMarker;
        }

        this.marker[i] =   new OpenLayers.Marker(
                (new OpenLayers.LonLat( loc[this.lonfield], loc[this.latfield])).transform(map.displayProjection, map.projection ),
                icon.clone());
        this.marker[i].Nid = loc[this.idfield];
        this.marker[i].loc = loc;
        //marker.setOpacity(0.2);
        if (this.canSelect || this.clickMarker){
            this.marker[i].events.register('mousedown', this.marker[i], function(evt) {
                ref_this.select(this.Nid,true);
            });
        }
        if (this.onMouseOver){
            this.marker[i].events.register('mouseover', this.marker[i], function(evt) {
		console.log("1 TOOLTIP MARKER");
                ref_this.onMouseOver(this,evt);
            });
        }
        if (this.onMouseOver){
            this.marker[i].events.register('mouseout', this.marker[i], function(evt) {
		console.log("1 TOOLTIP MARKER");
                ref_this.onMouseOut(this,evt);
            });
        }
        
    } catch (e) { Log.logInfo(e);}
}

NMarkerOverlay.prototype.select = function(id,doCallback) {
    var nr = this.marker.findIndex('Nid',id);
    if (nr < 0 ) {
    	console.log('can not find marker to select');
        return;
    }
    if (doCallback == null) {doCallback = true;}
    if (this.canSelect) {
        var marker_ref = this.marker[nr];
        if (!this.marker[nr].selected) {
            if (!this.multipleSelect) {

                if (this.selectedMarker[0] != null) {
                    this.marker[this.selectedMarker[0].nr].selected = false;
                    this.selectedFrame.removeMarker(this.selectedMarker[0]);
                    this.selectedMarker[0].destroy();
                    this.selectedMarker[0] = null;
                }
                this.selectedMarker = new Array();
            }
            //add 2 selected
            if (this.legend) {
                var icon = this.legend.getIcon(marker_ref.loc[this.legendField],true);
            } else {
                var icon = this.defaultSelectedMarker;
            }

            var selectedNr = this.selectedMarker.push(  new OpenLayers.Marker(
                (marker_ref.lonlat),
                icon.clone()))-1;

            this.selectedMarker[selectedNr].nr = nr;
            this.selectedMarker[selectedNr].Nid = id;
            this.selectedFrame.addMarker(this.selectedMarker[selectedNr]);
            //var selectedMarker_ref = this.selectedMarker[selectedNr];
            marker_ref.selected = true;
            var this_ref = this;

            if (this.canUnselect) {
                var id_ref = id
                this.selectedMarker[selectedNr].events.register('mousedown', this.selectedMarker[selectedNr], function(evt){
					this_ref.deselect(id)
                });
            }
            if (this.clickMarker != null && doCallback) {
                this.clickMarker(true,this.marker[nr],this.marker[nr].loc);
            }
        }

    }
}

NMarkerOverlay.prototype.deselect = function(id) {
	var nrSelected = this.selectedMarker.findIndex('Nid',id);
	if (nrSelected < 0) {
		console.log('can not find marker to unselect');
		return;
	}
 	var nrMarker = this.selectedMarker[nrSelected].nr;
	this.selectedFrame.removeMarker(this.selectedMarker[nrSelected]);
	this.selectedMarker[nrSelected].destroy();
	delete this.selectedMarker[nrSelected];
	if (this.clickMarker  != null) {
 		this.clickMarker(false,this.marker[nrMarker],this.marker[nrMarker].loc);
	}
	this.marker[nrMarker].selected = false;
}


NMarkerOverlay.prototype.addByData = function(data) {
    this.data = data;
    this.isPreLoaded = false;
}

NMarkerOverlay.prototype.refreshByData = function(data,filter) {
    this.clearAll();
    this.data = data;
    this.filter = filter
    this.isPreLoaded = false;
    this.preLoad();
}

NMarkerOverlay.prototype.preLoad = function() {

    if (!this.isPreLoaded) {
        this.isPreLoaded = true;
        var imarker = 0;
        if (this.isDataTreeFormat) {
            for (var idx = 0; idx < this.data.length; idx++) {
                var root = this.data.get(idx);
                for (var idc = 0; idc < root.children.getLength(); idc++) {
                    if (root.children) {
                        this._createMarker(imarker, root.children[idc]);
                        this.frame.addMarker(this.marker[imarker]);
                        imarker++;
                    }
                }
            }
        }
        else {
            for (var idx = 0; idx < this.data.length; idx++) {
            	if (!this.labelIsPoint || this.data[idx][this.labelIsPoint] == true) {
            		//use filter
            		if (this.filter == null || this.data[idx][this.filter.field] == this.filter.value) {
            			this._createMarker(imarker, this.data[idx]);
                		this.frame.addMarker(this.marker[imarker]);
                		imarker++;
                	}
                } 
            }
        }
    }
    return true;
}

//ok
NMarkerOverlay.prototype.show = function() {
    this.preLoad();
    if (!this.isLayerAddedToMap) {
    	this.addToMap();
    }

    try {
        this.frame.setVisibility(true);
        this.showLegendSection();
    } catch (e){
        console.log(e);
    }
}

NMarkerOverlay.prototype.hide = function() {
    try {
        this.frame.setVisibility(false);
        this.hideLegendSection();
    } catch (e){
        console.log(e);
    }
}

NMarkerOverlay.prototype.clearAll = function(doClearMain,doClearSelected) {
    this.removeFromMap();
    this.data = null;
    for (var idx=0; idx<this.marker.getLength(); idx++) {
         try {
             this.frame.removeMarker(this.marker[idx]);
             this.marker[idx].destroy();
         } catch (e) { console.log(e);}
     }

    this.marker = new Array();
    this.data = new Array();

    //TO DO: voor meerdere markers die geselecteerd kunnen worden. iets efficienter aub
     if (this.selectedFrame != null) {
        for (var idx=0; idx<this.selectedMarker.getLength(); idx++) {
            try {
                this.selectedFrame.removeMarker(this.selectedMarker[idx]);
                this.selectedMarker[idx].destroy();
            } catch (e) { console.log(e);}
        }
        this.selectedMarker = new Array();
     }



}

NMarkerOverlay.prototype.getSelected = function() {


}


NMarkerOverlay.prototype.addToMap = function() {
    if (!this.isLayerAddedToMap) {
        try {
            //this.layer.setOpacity( this.overlayManager.opacity );
    		this.frame.lizard_index = this.layerIndex;
            this._map.addLayer(this.frame);
            this.isLayerAddedToMap = true;
            if (this.selectedFrame && !this.isSelectedLayerAddedToMap) {
                this.selectedFrame.lizard_index = this.layerIndex + 1;
                this._map.addLayer(this.selectedFrame);
                this.isSelectedLayerAddedToMap = true;
            }
            this._map.reorder_layers();
        } catch (e){
            console.log(e);
        }
    }
}

NMarkerOverlay.prototype.removeFromMap = function() {
    if (this.selectedFrame && this.isSelectedLayerAddedToMap) {
        try {
            this._map.removeLayer(this.selectedFrame);
            this.isSelectedLayerAddedToMap = false;
        } catch (e){
            console.log(e);
        }
    }
    if (this.isLayerAddedToMap) {
        try {

            this._map.removeLayer(this.frame);
            this.isLayerAddedToMap = false;
        } catch (e){
            console.log(e);
        }
    }
}

NMarkerOverlay.prototype.setOpacity = function(opacity){
    if (this.frame) {
        this.frame.setOpacity(opacity);
    }
}
