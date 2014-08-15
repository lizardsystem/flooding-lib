console.log('loading NToolbar ...');

/****************************************************************************/
/**** class: 		NToolbar        		            	                */
/**** description: 	This class represents a toolbar, i.e. a set of          */
/****               buttons belonging to an application, like zooming etc.  */
/****************************************************************************/

function NToolbar(options) {
    var options = options || {};
    
    this.id = Nget_id();
    this.name = options.name || "";
    this.initFunction = options.initFunction || null;    
	this.isInit = false; 
	this.isAdded = false; //let op, deze wordt direct bewerkt door NToolbarManager
}

/**** Initializing the NToolbar ****/
NToolbar.prototype.init = function() {
	
	var initOptions = eval(this.initFunction+"()");
	this.tools = initOptions.tools || [];
    this.showForApplications = initOptions.showForApplications || [];
	this.isInit = true;
}

NToolbar.prototype.destroy = function() {
}

/**** Returns the tools that are contained within the NToolbar ****/
NToolbar.prototype.getTools = function() {
	if (!this.isInit ) {
		console.log("auto init NToolbar " + this.name);
		this.init();
	}
	return this.tools;
}

console.log('loaded NToolbar successfully');