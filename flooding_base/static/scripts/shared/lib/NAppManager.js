console.log('NAppManager laden ...');

/********************************************************/
/**** class: 		NAppManager 						*/
/**** description: 	Managed multiple instances of Napp  */
/****				and creates the 'App' header  		*/
/********************************************************/

/*
 * @requires NApp.js
 *
 */

function NAppManager(appManagerName, appHeaderPaneID, subAppHeaderPaneId, settings) {
    console.log('Creating NAppManager');
    this.appManagerName = appManagerName;
    this.appManagerPaneID = appHeaderPaneID;
    this.subAppHeaderPaneId = subAppHeaderPaneId;

    this.appList = {};
    this.selectedApp = null;
    this.mainScreen = {};
    settings = settings || {};

    this.mainScreenManager = settings.mainScreenManager || null;
    this.overlayManager = settings.overlayManager || null;
    this.toolbarManager = settings.toolbarManager || null;
    this.infoWindowManager = settings.infoWindowManager || null;
    this.rootUrl = settings.rootUrl || "/";
}

/**** Initialize the function ****/
NAppManager.prototype.init = function() {
    this.refresh();
}

NAppManager.prototype.destroy = function() {
    this.mainScreenManager.destroyMap();
}

/**** Returns the HTML for describing the header of the website, that displays the applications as links ****/
NAppManager.prototype.toHtml = function() {
    var firstLine = '<app1>';
    var secondLine = '';
    for (var app_id in this.appList) {
        var app = this.appList[app_id];

        if (app == this.getSelectedMainApp())
        {
            firstLine += '<b>'+app.name+'</b>&nbsp&nbsp&nbsp&nbsp';
            for (var subApp_id in app.subApps) {
                var subApp = app.subApps[subApp_id];
                //debugger;
                if (app.selectedSubApp == subApp) {
                    secondLine += '<b>'+subApp.name+'</b>&nbsp&nbsp';
                } else {
                    secondLine += '<a href="javascript:'+this.appManagerName+'.selectApp(\''+subApp.id+'\',\''+app.id+'\')">'+subApp.name+'</a>&nbsp&nbsp';
                }
            }
        } else {
            firstLine += '<a href="javascript:' + this.appManagerName + '.selectApp(\'' + app.defaultSubAppId + '\', \'' + app.id + '\' )">' + app.name + '</a>&nbsp&nbsp&nbsp&nbsp';
        }
    }
    return {firstline: firstLine +'</app1>', secondline: '<app2>' + secondLine + '&nbsp</app2>'};
}

/**** Sets a welcome text on the screen, for example if a user enters the application for the first time ****/
NAppManager.prototype.setStartPageText = function() {
    text = "Welkom op de Lizard-webinterface. U heeft momenteel toegang tot de volgende applicaties:<br><table>";
    for (var app_id in this.appList) {
        app = this.appList[app_id];
        text += "<tr><td>" + app.name + "</td><td>" + app.description + "</td></tr>";
    }
    text += "<table>";
    this.setScreen(FRAME);
    this.mainScreen[FRAME].setContents(text);
}

/**** Refreshes the App header ****/
NAppManager.prototype.refresh= function() {
    console.log('Refreshing App-header')
    lines = this.toHtml();
    document.getElementById(this.appManagerPaneID).innerHTML = lines.firstline;
    document.getElementById(this.subAppHeaderPaneId).innerHTML = lines.secondline;
}

/**** Add app to App Manager ****/
NAppManager.prototype.addApp= function(app) {
    // console.assert(this.appList[app.id] == null, "The id of this application is already used in the list of applications.");
    this.appList[app.id] = app;
}

/**** Add multiple apps to App Manager ****/
NAppManager.prototype.addApps= function(apps) {
    for (var i = 0 ; i < apps.length; i++) {
        this.addApp(apps[i]);
    }
}

/**** Remove app from App Manager ****/
NAppManager.prototype.removeApp= function(app) {
    if(this.appList[app.id]==null)
    {
    	console.warning("Application id does not exisit in the list of application id's!" )
    }
    delete this.appList[app.id];
}

/**** Select application (i.e. make the application active )                 ****/
/**** Parent_id is the id of the parent of the application having the app_id ****/
NAppManager.prototype.selectApp= function(app_id, parent_id) {
    console.log("entering method selectApp with parameters app_id=" + app_id + " and parent_id=" + parent_id);
    this.unselectApp();

    if (typeof(parent_id) == 'undefined') {
        this.selectedApp = this.appList[app_id];
        if (this.selectedApp.selectedSubApp) {
            this.selectedApp  = this.selectedApp.selectedSubApp;
        }
    } else { //search parent
	if (typeof(this.appList[parent_id]) == 'undefined') {
            alert('Configureerfout, applicatie "'+parent_id+'" bestaat niet. Contacteer systeembeheerder.');
	    return;
        } else if (typeof(this.appList[parent_id].subApps[app_id]) == 'undefined'){
	    alert('Configureerfout, subapplicatie "'+app_id+'" onder applicatie "'+parent_id+'" bestaat niet. Contacteer systeembeheerder.');
	    return;
        } else {
            this.selectedApp = this.appList[parent_id].subApps[app_id];
            this.appList[parent_id].selectedSubApp = this.selectedApp;
        }
    }

    //todo: register app_id and parent_id with server
    // func(app_id, parent_id)...

    //change mainscreen (voor overlayContainer)

    this.mainScreenManager.setScreen(this.selectedApp.screenType, this.selectedApp);

    if (!this.selectedApp.isInit) {
        this.selectedApp.init();
    }

    if (this.selectedApp.navigation) {
        scMain.showMember(scNavigation);
        scNavigation.setShowResizeBar(true);
        this.selectedApp.navigation.show();
    } else {
        scMain.hideMember(scNavigation, null);
        scNavigation.setShowResizeBar(false);
    }
    //scMain.redraw();

    if (this.infoWindowManager ) {
    	this.infoWindowManager.setWindows(this.selectedApp.infoWindowContainer);
    }

    if (this.selectedApp.overlayContainer) {
    	this.selectedApp.overlayContainer.addOverlays();
    }

    if (this.selectedApp.overlayManager) {
    	this.selectedApp.overlayManager.setMap(this.mainScreenManager.getMap())
    	this.selectedApp.overlayManager.show();
    }

    if (this.toolbarManager ) {
    	this.toolbarManager.setToolbar(this.selectedApp.toolbar);
    }

    this.selectedApp.onSelect();
    //refresh header
    this.refresh();

    this.selectedApp.onShow();
}

/**** Deselect application (does not change screen!)  ****/
NAppManager.prototype.unselectApp= function() {

    if (this.selectedApp && this.selectedApp.overlayContainer) {
    	this.selectedApp.overlayContainer.removeOverlays();
    }

    if (this.selectedApp && this.selectedApp.overlayManager) {
    	this.selectedApp.overlayManager.hide();
    }

    if (this.selectedApp != null) {
        this.selectedApp.onUnselect();
    }
    this.selectedApp = null;
}

/****  Get reference to selected NApp ****/
NAppManager.prototype.getSelectedApp= function() {
    if (!this.selectedApp) { return null; }
    return this.selectedApp.parentApp;

}

/****  Register app in server ****/
NAppManager.prototype.registerApp = function(site_name, url) {
    RPCManager.sendRequest({
	actionURL: url,
	useSimpleHttp: true,
	httpMethod: "GET",
	params: {app_name: this.selectedApp.id,
		 action: "set_current_subapplication",
	         site_name: site_name},
	callback: function(response, data, request) {
	}
    });
}

/****  Get reference to selected or parent of selected NApp ****/
NAppManager.prototype.getSelectedMainApp= function() {
    if (!this.selectedApp) { return null; }
    if (this.selectedApp.hasParentApp) {
        return this.selectedApp.parentApp;
    } else {
        return this.selectedApp;
    }
}

/****  Get reference to selected or child of selected NApp ****/
NAppManager.prototype.getSelectedSubApp= function() {
    if (!this.selectedApp) { return null; }
    if (this.selectedApp.hasParentApp) {
        return this.selectedApp;
    } else {
        return null;
    }
}

/**** Close the application tab ****/
NAppManager.prototype.closeAppTab= function(tab) {
    scNavigation.removeTab(tab);
    tab.app.scNavigation.isAdded = false;

}
console.log('NAppManager geladen ...');