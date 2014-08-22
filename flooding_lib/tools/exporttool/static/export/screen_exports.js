console.log('loading screen_exports ..');

/********************************************************************/
/**** script: 		screen_exports
/**** description: 	This script provides the functionaly to export
                        'waterdieptekaart'
/********************************************************************/

isc.Canvas.create({
    ID:'breadcrumbs',
    height:"15",
    contents: exporttool_config.breadcrumbs,
    autodraw:false
});

/*** DATASOURCES ***/
isc.DataSource.create({
    ID: "dsProjects",
    showPrompt: false,
    dataFormat: "json",
    dataURL: locationFloodingData,
    transformRequest: function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {action : 'get_projects'};
	    // combine paging parameters with criteria
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    recordXPath:"items",
    //autoFetchData:true,
    autoDraw:false,
    fields:[
	{name:"id", primaryKey:true, hidden:true, type:"int"},
	{name:"name", hidden: false, type:"text"}
    ]
});

isc.ResultSet.create({
    dataSource : "dsProjects"
});

isc.DataSource.create({
    ID: "dsScenariosExport",
    showPrompt: false,
    dataFormat: "json",
    dataURL: locationFloodingData,
    transformRequest: function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {action : 'get_scenarios_export_list'};
	    // combine paging parameters with criteria
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    autoFetchData:true,
    autoDraw:false,
    //clientOnly: false,
    fields:[
	{name:"scenario_id", primaryKey:true, hidden:false, type:"int"},
	{name:"scenario_name", hidden: false, type:"text"},
        {name:"scenario_approved", hidden: false, type: "boolean"},
	{name:"breach_ids", hidden: false, type:"text"},
	{name:"breach_names", hidden: false, type:"text"},
	{name:"region_ids", hidden: false, type:"text"},
	{name:"region_names", hidden: false, type:"text"},
	{name:"project_id", hidden: false, type:"int"},
	{name:"project_name", hidden: false, type:"text"},
	{name:"owner_id", hidden: false, type:"int"},
	{name:"owner_name", hidden: false, type:"text"},
	{name:"extwrepeattime", type:"text"},
	{name:"extwname", type:"text"},
	{name:"extwtype", type:"text"},
	//{name:"calcmethod", type:"text"},
	//{name: "statesecurity", type: "text"},
        //{name: "shelflife", type: "text"},
	{name: "_visible", hidden: true, type: "text"}
    ]
});

isc.ResultSet.create({
    dataSource : "dsScenariosExport"
});

var LoadScenariosForProject = function(projectId){
    msg.animateShow();
    dsScenariosExport.transformRequest= function (dsRequest) {
    	if (dsRequest.operationType == "fetch") {
    	    var params = {action : 'get_scenarios_export_list', project_id: projectId};
    	    // combine paging parameters with criteria
    	    return isc.addProperties({}, dsRequest.data, params);
    	}
    };

    dsScenariosExport.fetchData({}, function(response, data, request){
	// call fetchData on list grid to
	// prepare the local store for filtering
	scenariosAllListGrid.setData(data);
    	scenariosAllListGrid.fetchData();
	msg.animateHide();
    });
};

/***
Callback function for form.
Defined in this file, since javascript execeution in the exports_new templates
does block showing of the HTML for some reason.
***/
window['exportRunCallbackFormFunction'] = function() {
    var length =  scenariosToExportListGrid.data.getLength();
    var scenarioIds = [];
    for (var i = 0;  i < length; i++){
	scenarioIds[i] = scenariosToExportListGrid.data[i].scenario_id;
    }

    sendingForm = document.forms["exportRunForm"];

    // Create the post parameters
    var postParams = [];
    for (var n = 0; n < sendingForm.elements.length; n++){
	//NOTE: !! use '.name' to get it working with 'out-of-the-box' django validation !!
	if (sendingForm.elements[n].type === "checkbox") {
	    postParams[sendingForm.elements[n].name] = sendingForm.elements[n].checked;
	} else {
	    postParams[sendingForm.elements[n].name] = sendingForm.elements[n].value;
	}
    }
    postParams['scenarioIds'] = JSON.stringify(scenarioIds);
    RPCManager.sendRequest({
	actionURL: exporttool_config.url_export_tool,
	useSimpleHttp: true,
	httpMethod: "POST",
	params: postParams,
	callback: function(response, data, request){
	    if (response.httpResponseCode == 200) {
		console.log("Data ophalen gelukt, tonen op scherm.");
		// check if we have to open it in the pane or in the complete window
		if(data.match('redirect_in_js_to_')){
		    url = data.replace('redirect_in_js_to_/', '');
		    window.location= '/' + url;
		}
		else {
		    exportRunHTMLPane.setContents(data);
		}
	    } else {
		console.log("Fout bij het ophalen van gegevens.");
	    }
	}
    });
}

/*** SPECIAL SCENARIO LISTGRID CLASS ***/
isc.defineClass("ScenariosListGrid", "ListGrid").addProperties({
    width: "45%",
    height: 450,
    cellHeight:24,
    imageSize:16,
    border:"1px solid gray",
    bodyStyleName:"normal",
    loadingDataMessage: "Data aan het laden...",
    alternateRecordStyles:true,
    showHeader:true,
    leaveScrollbarGap:false,
    dataproperties: {
    	useClientFiltering: true
    	//useClientSorting: true
    }
});

isc.DynamicForm.create({
    ID:"projectSelector",
    layoutAlign: "left",
    height: 48,
    width: 250,
    overflow:"visible",
    fields: [{
	name: "projectField",
	optionDataSource: dsProjects,
	type: "select",
	emptyDisplayValue: "Selecteer project",
	valueField:"id",
	title: "Project",
	showTitle: false,
	change: "LoadScenariosForProject(value);",
	displayField:"name"}],
    autodraw: true
});

isc.ScenariosListGrid.create({
    ID:"scenariosAllListGrid",
    autodraw:false,
    canDragRecordsOut: true,
    canAcceptDroppedRecords: true,
    canReorderRecords: true,
    dragDataAction: "move",
    overflow:"visible",
    dataSource: dsScenariosExport,
    useClientFiltering: true,
    useClientSorting: true,
    showFilterEditor:true,
    autoFetchData: false,
    fields:[
	{name: "scenario_id", title:"ID", type:"int"},
	{name: "scenario_name", title: "Scenario naam", type: "text"},
        {name: "scenario_approved", title: "Goedgekeurd", type: "boolean"},
	{name: "extwrepeattime", title: "Overschrijdings frequentie", type: "text"},
	{name:"extwname", title: "Naam buitenwater", type:"text"},
	{name:"extwtype", title: "Buitenwater type", type:"text"},
	{name: "region_names", title: "Regio's", type: "text"},
	{name: "breach_names", title: "Doorbraak locaties", type: "text"},
	//{name: "calcmethod", title: "Berekenigns methode", type: "text"},
	//{name: "statesecurity", title: "Standzekerheid kerineng", type: "text"},
        //{name: "shelflife", title: "Houdbaarheid scenario", type: "text"},
	{name: "_visible", title: "_Visible", type: "text", enabled: false, showIf: "false"}
    ],
    emptyMessage:"<br><br>Geen scenario's beschikbaar voor dit project."
});

var copyToExportGrid = function(){
    //Copy selected record to export listgrid
    //set the records to not-visible state.
    var gridData = scenariosAllListGrid.data.allRows;
    for (var i = 0; i < gridData.length; i++){
	if (gridData[i]._visible != "false"){
	    gridData[i]._visible = "true";
	}
    }
    var selectedRows = scenariosAllListGrid.getSelection();
    for (var i = 0; i < selectedRows.length; i++){
    	selectedRows[i]._visible = "false";
	scenariosToExportListGrid.data.add(selectedRows[i]);
    }
    scenariosAllListGrid.filterData({_visible: ""});
    scenariosAllListGrid.filterData({_visible: "true"});
}

var copyToAllGrid = function() {
    // Delete selected records from toexport listgrid
    // set the records in 'all' listgrid to visible state
    var gridData = scenariosAllListGrid.data.allRows;
    var selectedRows = scenariosToExportListGrid.getSelection()
    for (var i = 0; i < selectedRows.length; i++){
	for (var j = 0; j < gridData.length; j++){
	    if (gridData[j].scenario_id == selectedRows[i].scenario_id){
		gridData[j]._visible = "true";
	    }
	}
	scenariosToExportListGrid.data.remove(selectedRows[i]);
    }
    //refresh filter it removes all existing filters
    scenariosAllListGrid.filterData({_visible: ""});
    scenariosAllListGrid.filterData({_visible: "true"});
}

isc.Img.create({
    ID:"arrowRight",
    src: exporttool_config.root_url + "static_media/images/icons/arrow_right.png", width:32, height:32,overflow:"visible",
    //click:"scenariosToExportListGrid.transferSelectedData(scenariosAllListGrid)"
    click:"copyToExportGrid();"
});

isc.Img.create({
    ID:"arrowLeft",
    src: exporttool_config.root_url + "static_media/images/icons/arrow_left.png", width:32, height:32,overflow:"visible",
    //click:"scenariosAllListGrid.transferSelectedData(scenariosToExportListGrid)"
    click:"copyToAllGrid();"
});

isc.Label.create({
    ID:"msg",
    wrap:false,
    contents:"Data aan het laden ..."
})


isc.ScenariosListGrid.create({
    ID:"scenariosToExportListGrid",
    canDragRecordsOut: true,
    canAcceptDroppedRecords: true,
    canReorderRecords: true,
    overflow:"visible",
    fields:[
	{name: "scenario_id", title:"ID", type:"int"},
	{name: "scenario_name", title: "Scenario naam", type: "text"},
	{name: "extwrepeattime", title: "Overschrijdings frequentie", type: "text"},
	{name:"extwname", title: "Naam buitenwater", type:"text"},
	{name:"extwtype", title: "Buitenwater type", type:"text"},
	{name: "region_names", title: "Regio's", type: "text"},
	{name: "breach_names", title: "Doorbraak locaties", type: "text"}
	//{name: "calcmethod", title: "Berekenigns methode", type: "text"},
	//{name: "statesecurity", title: "Standzekerheid kerineng", type: "boolean"},
        //{name: "shelflife", title: "Houdbaarheid scenario", type: "text"}
    ],
    emptyMessage:"<br><br>Sleep scenario's hier heen voor export."
});


var getExportForm = function() {
    var contentsURL = ""
    if (exporttool_config.export_run_id != '' && exporttool_config.export_run_id != null) {
	contentsURL = exporttool_config.url_export_edit;
    } else {
	contentsURL = exporttool_config.root_url + "flooding/tools/export/newexport";
    }

    var exportForm = isc.HTMLPane.create({
	ID: "exportRunHTMLPane",
	width:"100%",
	overflow:"visible",
	border: "0px",
	contentsURL: contentsURL
    });
    return exportForm;
};

/*** Arrange UI elements ***/
isc.VLayout.create({
    width: "100%",
    height: "100%",
    autoDraw: true,
    membersMargin: 10,
    members: [
	breadcrumbs,
	isc.HStack.create({
	    membersMargin: 0,
	    overflow: "visible",
	    members:[projectSelector,
		     msg]
	}),
	isc.HStack.create({
	    membersMargin: 10,
	    height: 160,
	    overflow: "visible",
	    members:[
		scenariosAllListGrid,
		isc.VStack.create({
		    width: 32,
		    height: 74,
		    layoutAlign: "center",
		    membersMargin: 10,
		    members: [arrowRight,arrowLeft]}),
		scenariosToExportListGrid
	    ]}),
	getExportForm()
    ]
});
msg.hide();

var createExportRunDs = function(export_run_id){
    var ds = isc.DataSource.create({
	showPrompt: false,
	dataFormat: "json",
	dataURL: exporttool_config.url_export_scenarios,
	transformRequest: function (dsRequest) {
	    if (dsRequest.operationType == "fetch") {
		var params = {export_run_id : export_run_id};
		// combine paging parameters with criteria
		return isc.addProperties({}, dsRequest.data, params);
	    }
	},
	autoFetchData:false,
	autoDraw:false,
	fields:[
	    {name:"scenario_id", primaryKey:true, hidden:false, type:"int"},
	    {name:"scenario_name", hidden: false, type:"text"},
	    {name:"breach_ids", hidden: false, type:"text"},
	    {name:"breach_names", hidden: false, type:"text"},
	    {name:"region_ids", hidden: false, type:"text"},
	    {name:"region_names", hidden: false, type:"text"},
	    {name:"project_id", hidden: false, type:"int"},
	    {name:"project_name", hidden: false, type:"text"},
	    {name:"owner_id", hidden: false, type:"int"},
	    {name:"owner_name", hidden: false, type:"text"},
	    {name:"extwrepeattimeser", type:"text"},
	    {name:"extwname", type:"text"},
	    {name:"extwtype", type:"text"},
	    {name: "_visible", hidden: true, type: "text"}
	]
    });
    return ds;
}


if (exporttool_config.export_run_id != '' && exporttool_config.export_run_id != null) {
    // Put scenarios into grids, set project
    var prField = projectSelector.getFields()[0]
    prField.setValue(exporttool_config.project_id);
    LoadScenariosForProject(exporttool_config.project_id);
    var dsExport = createExportRunDs(exporttool_config.export_run_id);
    msg.animateShow();
    dsExport.fetchData({}, function(response, data, request){
	// call fetchData on list grid to
	// prepare the local store for filtering
	scenariosToExportListGrid.setData(data);
	scenariosToExportListGrid.redraw();
	msg.animateHide();
    });
    dsExport.destroy();
}
