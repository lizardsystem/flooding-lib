console.log('loading NInfoWindow ...');

/************************************************************/
/**** class:         NInfoWindow                             */
/**** description:     This class contains the logic for the   */
/****               'floating' window on the screen.         */
/************************************************************/


HTMLPANE = 1;

function NInfoWindow(name,options) {
    this.id = Nget_id();
    this.name = name;

    options = options || {}
    this.tabName = options.tabName || name;
    this.defaultSize =  options.defaultSize || {width: 100, height:400 };

    this.canClose = options.canClose || false;
    this.canMax = options.canMax || false;
    this.canMin = options.canMin || false;
    this.showTitle = options.showTitle || false;
    this.preLoad = options.preLoad || false;
    this.enabled = (options.enabled != null)  ? options.enabled : true;

    //events
    this.onInit = options.onInit || function() {};
    this.onRefreshContent = options.onRefreshContent || function() {};
    this.onSelect = options.onSelect  || function() {};
    this.onUnSelect = options.onUnSelect || function() {};
    this.onDestroy = options.onDestroy || function() {};
    this.callbackFunctionPost =  options.callbackFunctionPost|| function() {};
    this.callbackFunctions =  options.callbackFunctionPost|| null;//object with callbackFunctions

    this.type = options.type || HTMLPANE;  //HTMLPane / IFRAME / CANVAS / FORM / CODE
    this.baseUrl = options.baseUrl || null; //the url of the page displayed in de infowindow
    this.params = options.params || null;
    this.isForm = options.isForm || false;

    this.paneId =  "info_window" + this.id;
    this.paneContentInSyncWithNavigation = false;

    this.pre_init();
    this.isInit = false;
}


/**** Pre-initializes the NInfoWindow (applying SmartClient settings) ****/
NInfoWindow.prototype.pre_init = function() {
    if (this.type = HTMLPANE) {
        var this_ref = this;
        this.pane = isc.HTMLPane.create({
            ID: "pane"+this.paneId,
            width: "100%",
            height: "100%",
            contentsURL:this.getActionSpecificUrl(),
            border: "none",
            overflow:"auto",
            contentLoaded: function() {
                try {
                    eval('infowindow_create' + this_ref.getFormId()+ '()');
                } catch (e){
                    console.log(e)
                };
            },
            autoDraw: true // Note: needed for creating the pane object with all its content
        });

    }

    // callbackFunctionPostOwner refers to the NInfoWindow instance that has
    // created the callbackFunctionPost. It is needed to refer to as 'this' can
    // not be used in the function as it will not refer to the NInfoWindow instance.
    // An other option would have been to give extra parameters to the function, but
    // for simplicity we've chosen this option.
    var callbackFunctionPostOwner = this;
    this.callbackFunctionPost = function() {

        sendingForm = document.forms[callbackFunctionPostOwner.getFormId()];
        // Create the post parameters
        var postParams = callbackFunctionPostOwner.params;
        postParams['callback'] = callbackFunctionPostOwner.getKeyOfCallbackFunctionPost();
        postParams['formId'] = callbackFunctionPostOwner.getFormId();
        for (var n=0; n<sendingForm.elements.length; n++){
            //NOTE: !! use '.name' to get it working with 'out-of-the-box' django validation !!
            postParams[sendingForm.elements[n].name]=sendingForm.elements[n].value;
        }

        console.log(postParams)
        RPCManager.sendRequest({
            actionURL: callbackFunctionPostOwner.baseUrl,
            useSimpleHttp: true,
            httpMethod: "POST",
            params: postParams,
            callback: function(response, data, request){

                if (response.httpResponseCode == 200) {
                    console.log("Data ophalen gelukt, tonen op scherm.")
                    callbackFunctionPostOwner.pane.setContents(data);
                } else {
                    console.log("Fout bij het ophalen van gegevens.");
                }
            }
        });
    }
}

NInfoWindow.prototype.init = function() {
    this.isInit = true;
}

checkShowInfoWindowScreen = function(check){
    console.log('entering method "checkShowInfoWindowScreen" with "check" = ' + check)
    check = typeof(check) == 'undefined' ? true : check;

    if(check)
    {
        console.log('infoWindowManager.showWindowsIfNeeded();')
        infoWindowManager.showWindowsIfNeeded();
    }
}

/**** This function disables the NInfoWindow and instructs the  ****/
/**** infowWindowManager to redraw its windows                  ****/
NInfoWindow.prototype.disable = function(checkShowTabScreen){
    this.enabled = false;
    tab = infoWindowManager.tabSet.disableTab("tab_" + this.id);

    checkShowInfoWindowScreen(checkShowTabScreen);
}
/**** This function enables the NInfoWindow and instructs the   ****/
/**** infowWindowManager to redraw its windows                  ****/
NInfoWindow.prototype.enable = function(checkShowTabScreen){
    this.enabled = true;
    tab = infoWindowManager.tabSet.enableTab("tab_" + this.id);

    checkShowInfoWindowScreen(checkShowTabScreen);
}

NInfoWindow.prototype.destroy = function() {
    //let op callback functies
}

/**** Resizes the window to the default size of the NInfoWindow ****/
NInfoWindow.prototype.resize = function(oldHeight)
{
    //console.assert(informationWindow !=null, "Error: informationWindow is null !!")
    var newWidth = this.defaultSize.width;
    informationWindow.animateRect((informationWindow.getLeft() +  informationWindow.width - newWidth), informationWindow.getTop(), newWidth, informationWindow.height, 500);
}

/****  Add or update parameters ****/
NInfoWindow.prototype.addOrUpdateParams = function(newParams) {
    if (this.params == null) {
        this.params = {};
    }
    for (par in newParams) {
        this.params[par] = newParams[par];
    }
    this.paneContentInSyncWithNavigation = false;
    this.reloadIfNeeded();
}

/**** Returns a boolean indicating if this instance is the selected infoWindow ****/
NInfoWindow.prototype.isSelected = function(){
    try{
        return (this == infoWindowManager.currentWindows[tabSetInfoWindow.getSelectedTabNumber()]);
    }
    catch (error)
    {
        return false;
    }
}

/**** Reloads the page displayed in the NInfoWindow, but only if it is the active NInfoWindow and the window is out of sync ****/
NInfoWindow.prototype.reloadIfNeeded = function() {
    console.log('entering method "reloadIfNeeded"');

    if(!this.paneContentInSyncWithNavigation && this.isSelected())
    {
        console.log('reloading infowindow with id: ' + this.id);
        this.destroyContent();
        this.pane.setContentsURL(this.getActionSpecificUrl());
        this.paneContentInSyncWithNavigation = true;
    }
}

/**** Calls function in infowindow (if present) which destroys the content of the infowindow ****/
NInfoWindow.prototype.destroyContent = function() {
    if (typeof(window['infowindow_destroy' + this.getFormId()])!= 'undefined') {
        console.log('destroy function exist, destroy')
        eval('infowindow_destroy' + this.getFormId()+ '()');
    }
}


/**** Returns the url for the page to be shown based on the parameters
      e.g.: "flooding/infowindow?scenario=1&action=information"        ****/
NInfoWindow.prototype.getActionSpecificUrl = function() {
    console.log('entering method "getActionSpecificUrl"')

    var url = this.baseUrl;
    if (this.params != null) {
        url += '?';
        for (par in this.params) {
            url +=  par + '=' + this.params[par] +'&';
        }
        url=url.slice(0,-1); // remove the last '&'
    }
    if (this.isForm) {
        url += '&callback=' + this.getKeyOfCallbackFunctionPost();
        url += '&formId=' + this.getFormId();
        url += '&destroy_function=infowindow_destroy' + this.getFormId();
        url += '&create_function=infowindow_create' + this.getFormId();
        url += "&pane_id=pane"+this.paneId;
    }
    return url;
}

/**** Returns the registration key of the callbackfunction that can be used to retreive the function later ****/
NInfoWindow.prototype.getKeyOfCallbackFunctionPost = function() {
    var function_id = this.id + '_post';

    // First register function (see the documentation of the calling method)
    this.setCallbackFunction(function_id, this.callbackFunctionPost );
    return 'callbackFunctions["' + function_id + '"]()';
}

/**** Returns the id of the form, which is based on the id of the NInfoWindows that shows the form. ****/
NInfoWindow.prototype.getFormId = function() {
    return 'infoWindowForm' + this.id ;
}

/**** Register the callback function, such that it can be found in by the
      Javascript code written in the action element of the html forms. ****/
NInfoWindow.prototype.setCallbackFunction = function(id,funct) {
    if (typeof(window['callbackFunctions']) == 'undefined') {
        window['callbackFunctions'] = {};
    }
    window['callbackFunctions'][id] = this.callbackFunctionPost;
}

console.log('loaded NInfoWindow succesfully')
