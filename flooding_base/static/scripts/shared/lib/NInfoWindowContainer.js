console.log('loading NInfoWindowContainer ...')

/*************************************************************/
/**** class: 		NInfoWindowContainer				     */
/**** description: 	This class is the container for multiple */
/****	    		NInfoWindows.                            */
/*************************************************************/

function NInfoWindowContainer(options) {
    options = options || {};
    this.id = "infoWindowContainer" + Nget_id();
    this.name = options.name || "-";
    this.initFunction = options.initFunction || null;
    this.file = options.file || null;
    this.infoWindows = options.infoWindows || [];
    
    this.isInit = false;
    this.isAdded = false;
    this.tab = null;
    this.tabset = null;
    this.isContainer = true;

}

/**** Initializes the container ****/
NInfoWindowContainer.prototype.init = function() {
	if (this.isInit) {
		return;
	}
	
	this.infoWindows = this.infoWindows.concat(eval(this.initFunction+"()"));	
	this.isInit = true;
}

/**** Returns the infowindows that are contained by this container ****/
NInfoWindowContainer.prototype.getInfoWindows = function() {
    console.log('entering method "getInfwWindows"')
	if (!this.isInit ) {
		console.log("calling init InfoWindowContainer " + this.name);
		this.init();
	}	
	return this.infoWindows;
}



NInfoWindowContainer.prototype.destroy = function() {
}

console.log('loaded NInfoWindowContainer succesfully')