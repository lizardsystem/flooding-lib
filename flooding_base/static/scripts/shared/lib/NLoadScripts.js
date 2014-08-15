/*************************************************************/
/**** description: 	Load the Nelen & Schuurmands library     */
/****               (called NLibrary)                        */
/*************************************************************/

function NLoadScripts(root_url, options) {
	var options = options || {};
	this.core = options.core || false;
	this.base = options.base || false;
	this.fews = options.fews || false;
	this.flooding = options.flooding || false;
    this.flooding_sa = options.flooding_sa || false;
    this.flow = options.flow || false;
    this.gisviewer = options.gisviewer || false; 
 	this.mis = options.mis || false;
 	this.nhi = options.nhi || false;
 	this.site = options.site || "";
 	
    var singleFile = false;
    if(!singleFile) {
		var jsfiles = new Array()
		
		if(this.core){
			jsfiles = jsfiles.concat(
				"static_media/weblib/OpenLayers-2.12-rc7/OpenLayers.js",
				"get_translated_strings.js",
				"get_config.js?site="+this.site,
				"static_media/weblib/isomorphic/system/modules/ISC_Core.js",
			    "static_media/weblib/isomorphic/system/modules/ISC_Foundation.js",
			    "static_media/weblib/isomorphic/system/modules/ISC_Containers.js",
			    "static_media/weblib/isomorphic/system/modules/ISC_Grids.js",
			    "static_media/weblib/isomorphic/system/modules/ISC_Forms.js",
			    "static_media/weblib/isomorphic/system/modules/ISC_DataBinding.js",
				"static_media/Isomorphic_NenS_skin/load_skin.js",
				"static_media/scripts/shared/SCpatch.js",
				"static_media/scripts/shared/JSONparser.js"
			);
		}

        if (this.base) {
        	jsfiles = jsfiles.concat(	
				"static_media/scripts/shared/overlaymanager.js",				
				"static_media/scripts/shared/maptools.js",
				"static_media/scripts/shared/rd2wgs.js",
				"static_media/scripts/shared/lib/NGeneral.js",
	
	 			"static_media/scripts/shared/lib/NApp.js",
	 			"static_media/scripts/shared/lib/NAppManager.js",
	 			"static_media/scripts/shared/lib/NBlock.js",
	 			
	 			"static_media/scripts/shared/lib/NToolbar.js",
	 			"static_media/scripts/shared/lib/NToolbarManager.js",
	 			"static_media/scripts/shared/lib/NMainScreenManager.js",				
	 			"static_media/scripts/shared/lib/NInfoWindow.js",
	 			"static_media/scripts/shared/lib/NInfoWindowManager.js",
	 			"static_media/scripts/shared/lib/NNavigation.js",
	 			"static_media/scripts/shared/lib/NAnimationControl.js",
	 			"static_media/scripts/shared/lib/NOverlayContainer.js",	 			
	 			"static_media/scripts/shared/lib/NInfoWindowContainer.js",
	 			"static_media/scripts/shared/lib/NLegendSection.js",
	 			"static_media/scripts/shared/lib/NLegendInfoWindow.js",	 			
	 			
	 			"static_media/scripts/shared/lib/geo/NCloudManager.js",
	 			"static_media/scripts/shared/lib/geo/NOverlay.js",
	 			"static_media/scripts/shared/lib/geo/NAnimation.js",
	 			"static_media/scripts/shared/lib/geo/NGeoFunctions.js",
	 			"static_media/scripts/shared/lib/geo/NMarkerSymbology.js",
	 			"static_media/scripts/shared/lib/geo/NMapOverlay.js",
	 			"static_media/scripts/shared/lib/geo/NAnimatedMapOverlay.js",
	 			"static_media/scripts/shared/lib/geo/NMarkerOverlay.js",
	 			"static_media/scripts/shared/lib/geo/NWMSOverlay.js",
	 			"static_media/scripts/shared/lib/geo/NAnimatedWMSOverlay.js"
	 		);
	 	}
	 	if (this.fews) {
 			jsfiles = jsfiles.concat(
  				"static_media/scripts/fews/app.js",
 				"static_media/scripts/fews/map/overlaySettings.js",
 				"static_media/scripts/fews/toolbar.js",
 				"static_media/scripts/fews/navigation.js"
 			);
 		}	
 		if (this.flooding) {
	 		jsfiles = jsfiles.concat(
	 			"static_media/scripts/flooding/app.js",
	 			"static_media/scripts/flooding/new/infoWindow.js",
	 			"static_media/scripts/flooding/new/navigation.js",
	 			"static_media/scripts/flooding/new/overlaySettings.js",
	 			"static_media/scripts/flooding/new/toolbar.js", 		
	 		 	
	 		 	"static_media/scripts/flooding/results/infoWindow.js",
	 			"static_media/scripts/flooding/results/navigation.js",
	 			"static_media/scripts/flooding/results/overlaySettings.js",
	 		    "static_media/scripts/flooding/results/toolbar.js",
			    "static_media/scripts/flooding/results/search.js",
			    "static_media/scripts/flooding/results/screen_keringen.js"
	 		);
 		}
 		if (this.flow) {
	 		jsfiles = jsfiles.concat(
	 			"static_media/scripts/flow/app.js",			 		 	
	 		 	"static_media/scripts/flow/results/infoWindow.js",
	 			"static_media/scripts/flow/results/navigation.js",
	 			"static_media/scripts/flow/results/overlaySettings.js",
	 			"static_media/scripts/flow/results/toolbar.js"
	 		);
 		}
 		
 		if (this.gisviewer) {
	 		jsfiles = jsfiles.concat(
	 			"static_media/scripts/gisviewer/app.js",			 		 	
	 			"static_media/scripts/gisviewer/map/navigation.js",
	 			/*"static_media/scripts/gisviewer/map/infoWindow.js",
	 			"static_media/scripts/gisviewer/map/overlaySettings.js",*/
	 			"static_media/scripts/gisviewer/map/toolbar.js"
	 		);
 		}
 		
 		if (this.mis) {
	 		jsfiles = jsfiles.concat(
	 			"static_media/scripts/mis/app.js",			 		 	
	 			"static_media/scripts/mis/map/navigation.js",
	 			"static_media/scripts/mis/map/infoWindow.js",
	 			"static_media/scripts/mis/map/toolbar.js",
	 			"static_media/scripts/mis/report/navigation.js",
	 			"static_media/scripts/mis/table/navigation.js"
	 		);
 		}
 		
 		if (this.nhi) {
	 		jsfiles = jsfiles.concat(
	 			"static_media/scripts/nhi/app.js",			 		 	
	 			"static_media/scripts/nhi/map/navigation.js",
	 			"static_media/scripts/nhi/map/infoWindow.js",
	 			"static_media/scripts/nhi/map/toolbar.js"	 			
	 		);
 		} 
 		 		
 		if (this.flooding_sa) {
 			jsfiles = jsfiles.concat(
	  			"static_media/scripts/flooding_standalone/app.js",
	 			"static_media/scripts/flooding_standalone/infoWindow.js",
	 			"static_media/scripts/flooding_standalone/navigation.js",
	 			"static_media/scripts/flooding_standalone/overlaySettings.js",
	 			"static_media/scripts/flooding_standalone/toolbar.js"
 			);			
 		}	

        var agent = navigator.userAgent;
        var docWrite = (agent.match("MSIE") || agent.match("Safari"));
        if(docWrite) {
            var allScriptTags = new Array(jsfiles.length);//2*
        }
 
        for (var i=0, len=jsfiles.length; i<len; i++) {
            var percentage = Math.round(((i+1)/jsfiles.length)*100);
            
            if (docWrite) {
                allScriptTags[i] = "<script src='" + root_url + jsfiles[i] +
                                   "'></script>";
                //allScriptTags[2*i+1] = "<script>setLoadMessage('laden..." + percentage + "%');</script>";
                                   
            } else {
                var s = document.createElement("script");
                s.src = root_url + jsfiles[i];
                var h = document.getElementsByTagName("head").length ? 
                           document.getElementsByTagName("head")[0] : 
                           document.body;
                h.appendChild(s);
                //var m = document.createElement("script");
                //m.text = "setLoadMessage('laden..." + percentage + "%');";
                //h.appendChild(m);
            }
            

        }
        if (docWrite) {
        	//allScriptTags.push("<script>removeLoadMessage();</script>");
            document.write(allScriptTags.join(""));
        } else {
                /*var m = document.createElement("script");
                m.text = "removeLoadMessage();";
                var h = document.getElementsByTagName("head").length ? 
                           document.getElementsByTagName("head")[0] : 
                           document.body;
                h.appendChild(m);*/

        }
    }
}

/**
 * Constant: VERSION_NUMBER
 */
NLoadScripts.VERSION_NUMBER="$Revision: 8012 $";
