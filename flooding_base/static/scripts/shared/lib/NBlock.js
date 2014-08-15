console.log('NBlock laden ...');

/****************************************************************************/
/**** class: 		NBlock 					                            	*/
/**** description: 	Combine and set default settings for                    */
/****				a combination of smartclient classes which form a       */
/****				tree in the left navigation balk of the interface  		*/
/****************************************************************************/

/*
 * @requires Isomorfic Smartclient
 *
 */

var NBlock = function (name, title, datasourceSettings, treeSettings, labelSettings, useResetButton) {
    this.name = name;
    this.title = title;
    this.useResetButton = useResetButton;

    labelSettings = labelSettings || {};

    this.ds = isc.DataSource.create(this.getSettings(datasourceSettings,this.defaultDatasourceSettings() ));
    this.label = isc.Label.create(this.getSettings(labelSettings, this.defaultLabelSettings() ));
    this.tree = isc.TreeGrid.create(this.getSettings(treeSettings, this.defaultTreeSettings() ));
    this.labelLayout = isc.HLayout.create({height: 24, styleName: "textItem", members: [this.label]});
    if (useResetButton) {
        btR = isc.IButton.create({
	    autoFit: true,
	    icon: "/static_media/Isomorphic_NenS_skin/images/actions/refresh.png",
	    click : function () { 
		resetNavigationBlocks();
	    }
	});
	this.labelLayout.addMember(btR);
    }
};

/**** Returns the default settings for the datasource ****/
NBlock.prototype.defaultDatasourceSettings = function() {
    var defaultSettings = {
        showPrompt:false,
        dataFormat:"json",
        dataTransport : "xmlHttpRequest",
        callbackParam : "callback",
        autoFetchData:false,
        autoDraw:false
    };
    return defaultSettings;
};

NBlock.prototype.defaultLabelSettings = function() {
    var defaultSettings = {
        // ***gespecificeerd***
        title: this.title,
        contents: this.getLabelString,
        // ***standaard***
        showFocusedAsOver:false,
        wrap:false,
        left:10,
        height:24,
        //styleName:"textItem",
        overflow:"hidden",
        autoDraw:false,
        top:5,
        dynamicContents:true,
        showTitle:false,
        showFocused:false
    };
    return defaultSettings;
};

NBlock.prototype.defaultTreeSettings = function() {
    var defaultSettings = {
        treeFieldTitle: this.name,
        dataSource:this.ds,
        showRoot:false,
        separateFolders:false,
        loadingDataMessage:ST_LOADING_DATA,
        canReorderFields:false,
        canResizeFields:false,
        showHeader:false,
        showHeaderContextMenu:false,
        loadDataOnDemand:false,
        overflow:"auto",
        autoFetchData:false,
        autoDraw:false
    };
    return defaultSettings;
};

/**** Returns the specific setting, but the unknown variables in the specific setting are filled with these from the defaultsettings  ****/
NBlock.prototype.getSettings = function( specificSettings, defaultsettings ) {
    for (set in defaultsettings) {
        specificSettings[set] = specificSettings[set] || defaultsettings[set];
    }
    return specificSettings;
}

/**** Returns the HTML for visualizing the label that is shown as header in the block ****/
NBlock.prototype.getLabelString= function( value ) {
    value = value || ST_SELECT;
    return "   <b>"+this.title+": </b><i>"+value+ "</i>";
}

/**** Creates the label (header of a block)) for a specific value and set it as content ****/
NBlock.prototype.setLabel= function(value) {
    this.label.setContents(this.getLabelString(value));
}

/**** Clears the tree in the block ****/
NBlock.prototype.clear= function(message) {
	this.setLabel(message);
	this.tree.setData([]);
}

/**** Returns the label (header of the block) and the tree to be shown in the block ****/
NBlock.prototype.getMembers = function() {
    return [this.labelLayout, this.tree];
}

/************** General Functions    **********************/
function loadScript(uri, dynamic, callback) {
    dynamic = false;
    callback = callback || function(){};

	var agent = navigator.userAgent;
	var docWrite = (agent.match("MSIE") || agent.match("Safari"));
	if(docWrite) {
		var allScriptTags = new Array(1);
	}
    var host = "";

	if (docWrite) {
		document.write("<script src='" + host + jsfiles[i] +
                          "'></script>");
	} else {
		var s = document.createElement("script");
		s.src = host + uri;
		var h = document.getElementsByTagName("head").length ?
                   document.getElementsByTagName("head")[0] :
                   document.body;
        h.appendChild(s);
    }
    callback();
    return true;
}


console.log('NBlock geladen');