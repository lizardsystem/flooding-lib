var OpenLayers = {};
var map = null;

/**** The method to be called after loading ****/
var afterLoad = function () {
    console.log('entering method "afterLoad()"');
    isc.RPCManager.addClassProperties({
	
         handleError : function (response, request) {
    	     console.log("ERROR BALA");
    	     var httpMethod = response.context.httpMethod;
    	     if ((httpMethod == 'GET') && (!request.floodingRetry || request.floodingRetry < 1)) {
                 var actionURL = response.context.actionURL;
                 var callback = response.context.callback;
                 var data = { action: request.data.action };
    		 var req = request;
    		 var res = response;
                 if (!request.floodingRetry) {
                     request.floodingRetry = 0;
                 } else {
                     request.floodingRetry++;
                 }
    		 isc.RPCManager.sendRequest({
    		     params: data,
    		     callback: callback,
    		     callback :function(resp, datas, resp) {
			 // fireReplyCallback occurs error 'willHandleError undefined'
    		     	 //isc.RPCManager.fireReplyCallback(callback, 'rpcResponse, data, rpcRequest', [ res, data, req ]);
    		     	 //isc.warn("Error on retrieving data. For wifi required STRONG internet connection.");
    		     },
    		     actionURL: actionURL,
    		     willHandleError: true,
    		     useSimpleHttp: true,
    		     httpMethod: httpMethod});
    	     }	     
    	 }
    });
    console.log('Loading Flooding application script');   
    var flooding = loadFloodingApp();
    toolbarManager = new NToolbarManager();
    infoWindowManager = new NInfoWindowManager('main', scPage, {} );
    appManager = new NAppManager("appManager", "appHeaderPane", "subAppHeaderPane", {
        toolbarManager:  toolbarManager,
        mainScreenManager:  mainScreenManager,
        infoWindowManager:  infoWindowManager,
        rootUrl: flooding_config.root_url
    });
    
    appManager.addApps([flooding]);
    appManager.init();
    appManager.selectApp("flooding");
    appManager.selectApp("floodingResults", "flooding");
};

var onUnload = function () {
    appManager.registerApp(flooding_config.sitename, flooding_config.uberservice_url);
    overlayManager = null;

    try {
        if (map) {map.destroy();};
    } catch (e) {
        console.log('during unload: ' + e);
    }
    try {
        scPage.destroy();
    } catch (e) {
        console.log('during unload: ' + e);
    }
};

var resizeTimeout = null;

var onResize = function () {
    if (resizeTimeout !== null) {
	window.clearTimeout(resizeTimeout);
	resizeTimeout = null;
    }
    resizeTimeout = window.setTimeout(function () {
	appManager.mainScreenManager.getMap().updateSize();
	if (typeof(infoWindowManager)!= 'undefined') {
            infoWindowManager.repositionWindow();
	}
        resizeTimeout = null;
    }, 500);
};
