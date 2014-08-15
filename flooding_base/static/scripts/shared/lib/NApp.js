console.log('start laden Appmanager.js');

/********************************************************/
/**** class: 		NApp         						*/
/**** description: 	An application that uses the web-   */
/****               interface.                          */
/********************************************************/


/* 
 * @requires OpenLayers/BaseTypes.js
 * @requires OpenLayers/Lang/en.js
 */ 


// General 'transformation' of values from python to javascript. 
True = true
False = false
None = -1

var map = null;

MAP = 1
IFRAME= 2
FRAME = 3

/**** Identity number generator - using the global variable Nget_id_nr ****/
Nget_id_nr = 0;
function Nget_id() {
    return Nget_id_nr++;
}

function NApp(name,options) {    
    this.id = options.id||Nget_id();
    this.name = name;
    
    options = options || {};
        
    this.description = options.description || "";
    this.screenType = options.screenType || FRAME;
    this.navigation =  options.navigation || null;
    this.overlayContainer = options.overlayContainer || null;
    this.overlayManager = options.overlayManager || null;
    this.infoWindowContainer =  options.infoWindowContainer || null;
    this.toolbar =  options.toolbar || null;
	this.defaultSubAppId = options.defaultSubAppId || null; 
    
    this.url = options.url || null;
    
    this.onInit = options.onInit || function() { };
    this.onShow = options.onShow || function() { };
    this.onHide = options.onHide || function() { };
    this.onUnselect = options.onUnselect || function() { };
    this.onSelect = options.onSelect || function() { };

    this.isInit = false;
    this.subApps = {};
    this.hasSubApps = false;
    this.parentApp = {};
    this.hasParentApp = false;
    this.selectedSubApp = null;
    
}

/**** Adds multiple applications as children to this application ****/
NApp.prototype.addSubApps = function(apps) {
    for (var i = 0 ; i < apps.length ; i++) {
        this.addSubApp(apps[i]);
    }
}

/**** Adds an application as a child to this application ****/
NApp.prototype.addSubApp = function(app) {
    if (!app.hasSubApps && !app.hasParentApp) {
        this.subApps[app.id] = app;
        this.hasSubApps = true;
        app.parentApp = this;
        app.hasParentApp = true;
    } else {
        console.error('Can not add App if it already has a child or parent)')
    }
}

/**** Select one of the subapplications of this application ****/
NApp.prototype.selectSubApp = function(app_id) {
    console.log('Selecting sub application with id:' + app_id)
    this.selectedSubApp = this.subApps[app_id];
}

/**** Initializes an application ****/
NApp.prototype.init = function() {
    console.log('Initializing application: ' + this.name)

    if (this.navigation && !this.navigation.isInit) {        
        this.navigation.init();
        this.navigation.addToTabSet(scNavigation);        
        this.navigation.show();
    }

 	if (this.infoWindowContainer && !this.infoWindowContainer.isInit) {
		this.infoWindowContainer.init();
    }  
    
    if (this.overlayContainer && !this.overlayContainer.isInit) {
        this.overlayContainer.init();
    }  
    
    if (this.toolbar && !this.toolbar.isInit) {
        this.toolbar.init();
    }  
    
    this.onInit();
    this.isInit = true;
}

/******************** To do *******************/
NApp.prototype.destroy = function() {
    this.isInit = false;
}
console.log('NApp geladen');
