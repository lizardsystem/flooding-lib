console.log('loading NOverlayContainer ...')

/********************************************************************/
/**** class: 		NOverlayContainer		            	        */
/**** description: 	This class contains multiple overlays.          */
/********************************************************************/

function NOverlayContainer(options) {
    options = options || {};
    this.id = Nget_id();
    this.name = options.name || "";

    this.initFunction = options.initFunction || function() {return []};
        
	this.isInit = false; 
	this.isAdded = false; //let op, deze wordt direct bewerkt door NToolbarManager
}

/**** Initializing the NOverlayContainer ****/
NOverlayContainer.prototype.init = function() {
	var overlays = [];
	try {
		overlays = (eval(this.initFunction+"()")).overlays;
	} catch (e) {}
    this.overlays = overlays  || [];
	this.isInit = true;

}

NOverlayContainer.prototype.destroy = function() {

}

NOverlayContainer.prototype.clear = function() {
	if (this.isAdded) {
		this.removeOverlays();
	}
	this.overlays = [];
}


NOverlayContainer.prototype.addOverlayToContainer = function(layer) {
    this.overlays.push(layer);
    if (this.isAdded) {
	this.overlays[this.overlays.length-1].addToMap(map);
	this.overlays[this.overlays.length-1].show();
	var layersList = map.getLayersByName(layer.name);
	layersList[0].show();
    }
}

NOverlayContainer.prototype.addOverlays = function() {
	if (!this.isInit ) {
		console.log("auto init NOverlayContainer " + this.name);
		this.init();
	}
	if (!this.isAdded) {
		for (var i = 0 ; i < this.overlays.length ; i++) {
			this.overlays[i].addToMap(map);
		}
	}
	this.isAdded = true;
}

NOverlayContainer.prototype.removeOverlays = function() {
	for (var i = 0 ; i < this.overlays.length ; i++) {
		try {
			this.overlays[i].removeFromMap();
		} catch (e){
			this.overlays[i].hide();
		}	
	}
	this.isAdded = false;	
}

NOverlayContainer.prototype.getLegendSections = function(){
	var options = {name:'testname', title:'testtitle', initialExpanded:false, contentsURL:'visualization/legend/?object_id=1'}
	
	return new NLegendSection('legendId', options);
}

console.log('loaded NOverlayContainer succesfully');
