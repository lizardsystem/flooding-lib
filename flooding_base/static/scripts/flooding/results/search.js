console.log('loading search window ..');

/********************************************************************/
/**** script: 		search
/**** description: 	This script provides the functionaly to 
                        search, filter scenarios
/********************************************************************/

var createSelectionDS = function(dS, actionParam){
    ds = isc.DataSource.create({
	ID: dS,
	showPrompt: false,
	dataFormat: "json",
	dataURL: locationFloodingData,
	autoFetchData: false,
	actionParam: actionParam,
	transformRequest: function (dsRequest) {
    	    if (dsRequest.operationType == "fetch") {
    		var params = {action : this.actionParam};
	    }
    	    return isc.addProperties({}, dsRequest.data, params);
	},
	fields:[
    	    {name:"id", primaryKey: true, type:"int" },
	    {name:"name", hidden: false, type:"text" }
	]
    });
}

var navigateToRegionOnMap = function(leaf) {
    /**
       zoom in region of provided leaf
       add the breaches to layer
    */
    Ozoom(map ,leaf );
    region_layers_results.clear();
    region_layers_results.addOverlays();
    dsListRegionMapsResults.fetchData({region_id:leaf.rid}, function(dsResponse, data, dsRequest){
	if (data.length > 0) {
	    for (var i=0; i<data.length; i++){
		var map = data[i];
		layer = new NWMSOverlay(map.id, map.name, {
		    rootURL:map.url,
		    singleTile:!(map.tiled),
		    layerIndex:20-i,
		    displayInLayerSwitcher: true,
		    geoType:3,
		    valueType:2,
		    getSettingsFromRequest: false,
		    getFramesFromRequest:true,
		    frameUrl:map.url,
		    app: 'flooding',
		    visible: false
		});
		region_layers_results.addOverlayToContainer(layer);
	    }
	}
    });
}

var refreshRegionMaps = function(regionid, leaf){

    region_layers_results.clear();
    region_layers_results.addOverlays();
    dsListRegionMapsResults.fetchData({region_id:regionid}, function(dsResponse, data, dsRequest){
	if (data.length > 0) {
	    for (var i=0; i<data.length; i++){
		var map = data[i];
		layer = new NWMSOverlay(map.id, map.name, {
		    rootURL:map.url,
		    singleTile:!(map.tiled),
		    layerIndex:20-i,
		    displayInLayerSwitcher: true,
		    geoType:3,
		    valueType:2,
		    getSettingsFromRequest: false,
		    getFramesFromRequest:true,
		    frameUrl:map.url,
		    app: 'flooding',
		    visible: false
		});
		region_layers_results.addOverlayToContainer(layer);
	    }

	    //Bestaande keringen, get_existing_embankments_shape,
	    //Hoogtekaart, action:'get_extra_grid_shapes', only_selected:True
	    //Bestaande keringen, action:'get_extra_shapes', only_selected:True
	}

    });
}

var breachLeafClickSearch = function(viewer, leaf, recordNum){

    if (leaf.isbreach === true) {
	breach_def = leaf.id;//to do, dit kan anders
        frBlockBreaches.setLabel(leaf.name);
        frbreachLayer.select(leaf.id,false);
        clear_scenarios();
        frLoccutoffsLayer.clearAll();
        frExtraEmbankmentLayer.hide();
        frBlockScenarios.tree.fetchData({breach_id:leaf.id, filter:floodingFilterResults}, function(request, data) {
	    for (var idx=0; idx<data.length; idx++) {
		if (data[idx].isFolder) {
		    frBlockScenarios.tree.openFolder(data[idx]);
		}
	    }
	flooding.preload.preload_scenario(frBlockScenarios.tree);
        });
	Ozoom(map ,leaf );
    region_layers_results.clear();
    region_layers_results.addOverlays();
    dsListRegionMapsResults.fetchData({region_id:leaf.rid}, function(dsResponse, data, dsRequest){
	if (data.length > 0) {
	    for (var i=0; i<data.length; i++){
		var map = data[i];
		layer = new NWMSOverlay(map.id, map.name, {
		    rootURL:map.url,
		    singleTile:!(map.tiled),
		    layerIndex:20-i,
		    displayInLayerSwitcher: true,
		    geoType:3,
		    valueType:2,
		    getSettingsFromRequest: false,
		    getFramesFromRequest:true,
		    frameUrl:map.url,
		    app: 'flooding',
		    visible: false
		});
		region_layers_results.addOverlayToContainer(layer);
	    }
	}
    });
    }
}

var scenarioLeafClickSearch = function(viewer, leaf, record) {
    return null;
}

var retrieveIDs = function(values){

    ids = new Array();
    for (var i = 0; i < values.length; i++) {
	ids[i] = values[i].id;
    }
    return ids;
}

var retrieveSearchParams = function(){
    var searchParams = {};
    var forms = searchForms.getMembers();
    for (var i = 0; i < forms.length; i++){
	var selectionField = forms[i].getField("selection");
	var searchByValue = forms[i].getField("searchBy").getValue();
	if (searchByValue == null) {
	    continue;
	}
	if (selectionField.pickList == null) {
	    continue;
	}
	var values = selectionField.pickList.selection.getSelection();
	if (values.length <= 0) {
	    continue;
	}	    
	searchParams[searchByValue] = retrieveIDs(values);	
    }
    return searchParams;
}

var isEmptyObject = function(obj) {
    for (prop in obj) {
	return false;
    }
    return true;
}

var applySearch = function() {
    var searchParams = retrieveSearchParams();
    var regionsTransformRequest = frBlockRegions.ds.transformRequest;
    var breachesTransformRequest = frBlockBreaches.ds.transformRequest;
    var scenariosTransformRequest = frBlockScenarios.ds.transformRequest;
    //var breachLeafClick = frBlockBreaches.tree.leafClick;
    frBlockRegions.ds.transformRequest = function(dsRequest) {
	if (dsRequest.operationType == "fetch"){
	    var params = {
		action: "get_region_tree_search",
		searchBy: searchParams
	    };
	    return isc.addProperties({}, dsRequest.data, params);
	}
    }
    //frBlockBreaches.tree.leafClick = breachLeafClickSearch;
    frBlockBreaches.ds.transformRequest = function(dsRequest) {
	if (dsRequest.operationType == "fetch"){
	    var params = {
		action: "get_breach_tree_search",
		filter: selectResultType.getValue(),
		searchBy: searchParams
	    };
	    return isc.addProperties({}, dsRequest.data, params);
	}
    }
    frBlockScenarios.ds.transformRequest = function(dsRequest) {
	if (dsRequest.operationType == "fetch"){
	    var params = {
		action: "get_scenario_tree_search",
		filter: selectResultType.getValue(),
		searchBy: searchParams
	    };
	    return isc.addProperties({}, dsRequest.data, params);
	}
    }
    if (frBlockRegions.tree.getData().isEmpty()) {
	frBlockRegions.tree.fetchData();
    } else {
	var rootRegions = frBlockRegions.tree.getData().root;
	frBlockRegions.tree.getData().reloadChildren(rootRegions);
    }
    frBlockRegions.ds.transformRequest = regionsTransformRequest;
    if (frBlockBreaches.tree.getData().isEmpty()) {
	frBlockBreaches.tree.fetchData();
    } else {
	var rootBreaches = frBlockBreaches.tree.getData().root;
	frBlockBreaches.tree.getData().reloadChildren(rootBreaches);
    }
    frBlockBreaches.ds.transformRequest = breachesTransformRequest;
    //frBlockBreaches.tree.leafClick = breachLeafClick;
    if (frBlockScenarios.tree.getData().isEmpty()) {
	frBlockScenarios.tree.fetchData();
    } else {
	var rootScenarios = frBlockScenarios.tree.getData().root;
	frBlockScenarios.tree.getData().reloadChildren(rootScenarios);
    }
    frBlockScenarios.ds.transformRequest = scenariosTransformRequest;
    frBlockResults.tree.data = [];
    frBlockResults.tree.redraw();
}

// var getSearchResult = function(){
//     isc.RPCManager.sendRequest(
// 	{
// 	    actionURL: locationFloodingData,
// 	    showPrompt: false,
// 	    httpMethod: "POST",
// 	    params: {"params": retrieveSearchParams(),
// 		     "action": "search_navigation_objects"},
// 	    callback: reqCallback,
// 	    dataFormat: "json",
// 	    useSimpleHttp: true
// 	});
// }

var updateNavigationWindows = function(){
    var params = retrieveSearchParams();

}

isc.IButton.create({
    ID: "btSubmit",
    title: ST_APPLY,
    autoFit: true,
    click : function () {
	var searchParams = retrieveSearchParams();
	if (isEmptyObject(searchParams)){
	    isc.warn(ST_EMPTY_SELECTION_WARN);
	} else {
	    emptyNavigationBlocks();
	    applySearch();
	    searchWindow.hide();
	}
    }
});

isc.IButton.create({
    ID: "btClose",
    title: ST_CLOSE,
    autoFit: true,
    click : function () { 
	searchWindow.hide();
    }
});

isc.IButton.create({
    ID: "btReset",
    title: ST_RESET,
    autoFit: true,
    click : function () { 
	clearSearchFields();
	resetNavigationBlocks();
    }
});

var emptyNavigationBlocks = function() {
    frBlockRegions.clear();
    frBlockBreaches.clear();
    frBlockScenarios.clear();
    frBlockResults.clear();
}

var resetNavigationBlocks = function() {
    if (frBlockRegions.tree.getData().isEmpty()) {
	    frBlockRegions.tree.fetchData();
    } else {
	regionsRoot = frBlockRegions.tree.getData().root;
	frBlockRegions.tree.getData().reloadChildren(regionsRoot);
    }
    frBlockRegions.tree.redraw();
    frBlockBreaches.clear();
    frBlockScenarios.clear();
    frBlockResults.clear();
}

var clearSearchFields = function(){
    forms = searchForms.getMembers();
    for (var i = 0; i < forms.length; i++){
	var selectionField = forms[i].getField('selection');
	var serchByField = forms[i].getField('searchBy');
	selectionField.clearValue();
	serchByField.clearValue();
	selectionField.setProperties({
	    "optionDataSource": null,
	    "emptyDisplayValue": ""
	});
	selectionField.redraw();
    }
}

var isUniqueChoice = function(value){
    /** 
	Return true when the value in searchBy field
	is not yet used.
    */
    var forms = searchForms.getMembers();
    var count = 0;
    for (var i = 0; i < forms.length; i++){
	var searchBy = forms[i].getField('searchBy');
	if (searchBy.getValue() == value){
	    count+=1;
	}
	if (count > 0) {
	    return false;
	}
    }
    return true;
}

var createSearchForm = function() {
    var form = isc.DynamicForm.create({
	autoDraw: false,
	fields: [
	    {
		name: "searchBy",
		title: ST_SEARCH + "&nbsp;" + ST_IN,
		valueMap: ['Project', 'Regio', 'Buitenwater'],
		type: "select",
		autoFit: true,
		overflow: 'hidden',
		emptyDisplayValue: ST_ALL_,
		leaveScrollBarGap: false,
		showAllOptions: true,
		change: function (f, i, v) {
		    var isUnique = isUniqueChoice(v);
		    var relField = f.getField('selection');
		    if (relField.pickList != null) {
			relField.setProperties({
			    "optionDataSource": null,
			    "emptyDisplayValue": ""
			});
			relField.clearValue();
			relField.redraw();
		    }
		    if (!isUnique) {
			isc.warn(ST_SEARCH_WARN_PART_1 + " '" + v + "' " + ST_SEARCH_WARN_PART_2);
			i.clearValue();
			relField.setProperties({
			    "optionDataSource": null,
			    "emptyDisplayValue": ""
			});
			relField.redraw();
			return;
		    }

		    if (v == 'Project') {
			relField.setProperties({
			    "optionDataSource": dSProjectSelection,
			    "emptyDisplayValue": ST_SELECT + " " + ST_PROJECT + "(s)"
			});
		    } else if (v == "Regio") {
			relField.setProperties({
			    "optionDataSource": dSRegionSelection,
			    "emptyDisplayValue": ST_SELECT + " " + ST_REGION_
			});
		    } else if (v == "Buitenwater") {
			relField.setProperties({
			    "optionDataSource": dSEWSelection,
			    "emptyDisplayValue": "Selecteer buitenwater(s)"
			});
		    }
		    relField.redraw();
		}
	    },
	    {
		name: "selection",
		title: ST_SELECTION,
		autoFetchData:false,
		cachePickListResults: false,
		valueField:"id",
		multiple:true,
		multipleAppearance:"picklist",
		type: "select",
		displayField:"name"
	    }
	]
    });
    return form;
}

createSelectionDS("dSProjectSelection", "get_projects_only");
createSelectionDS("dSRegionSelection", "get_all_regions");
createSelectionDS("dSEWSelection", "get_external_waters");

isc.HLayout.create({
    ID: "searchForms",
    membersMargin: 5,
    members: [
	createSearchForm(),
	createSearchForm(),
	createSearchForm()
    ]
});

isc.HLayout.create({
    ID: "buttons",
    layoutTopMargin: 20,
    membersMargin: 5,
    defaultLayoutAlign: "center",
    align: "center",
    members: [btReset, btClose, btSubmit]
});

isc.VLayout.create({
    ID: "searchMainLayout",
    layoutTopMargin: 10,
    layoutLeftMargin: 10,
    padding: 5,
    width: "600",
    members: [searchForms, buttons]
});

isc.Window.create({
    ID: "searchWindow",
    title: ST_SEARCH,
    autoSize:true,
    autoCenter: true,
    isModal: true,
    showModalMask: true,
    autoDraw: false,
    closeClick : function () {
	this.Super("closeClick", arguments)
    },
    items: [
	searchMainLayout
    ]
});
