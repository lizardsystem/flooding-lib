isc.Canvas.create({
    ID:'breadcrumbs',
    height:"15",
    contents: '{% spaceless %} <div class="breadcrumbs"> {% if breadcrumbs %}&rsaquo;{% endif %} {% for blitem in breadcrumbs %}{% if blitem.url %}<a href="{{ blitem.url }}">	{{ blitem.name }}</a> {% else %}{{ blitem.name }}{% endif %}{% ifnotequal forloop.revcounter0 0 %}&rsaquo;{% endifnotequal %} {% endfor %} </div>'
    ,{% endspaceless %}
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
    autoFetchData:false,
    autoDraw:false,
    fields:[
	{name:"scenario_id", primaryKey:true, hidden:true, type:"int"},
	{name:"scenario_name", hidden: false, type:"text"},
	{name:"breach_ids", hidden: false, type:"text"},
	{name:"breach_names", hidden: false, type:"text"},
	{name:"region_ids", hidden: false, type:"text"},
	{name:"region_names", hidden: false, type:"text"},
	{name:"project_id", hidden: false, type:"int"},
	{name:"project_name", hidden: false, type:"text"},
	{name:"owner_id", hidden: false, type:"int"},
	{name:"owner_name", hidden: false, type:"text"}
    ]
});

LoadScenariosForProject = function(projectId){
    dsScenariosExport.transformRequest= function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {action : 'get_scenarios_export_list', project_id: projectId};
	    // combine paging parameters with criteria
	    return isc.addProperties({}, dsRequest.data, params);
	}
    };
    dsScenariosExport.fetchData(null, function(response, data, request){
	scenariosAllListGrid.setData(data);
    });
}

/***
     Callback function for form.
     Defined in this file, since javascript execeution in the exports_new templates
     does block showing of the HTML for some reason.
***/
window['exportRunCallbackFormFunction'] = function() {
    var length =  scenariosToExportListGrid.data.getLength();
    var scenarioIds=[]
    for (var i =0;  i <length; i++){
	scenarioIds[i] = scenariosToExportListGrid.data[i].scenario_id;
    }

    sendingForm = document.forms["exportRunForm"];
    // Create the post parameters
    var postParams = [];
    for (var n=0; n<sendingForm.elements.length; n++){
	//NOTE: !! use '.name' to get it working with 'out-of-the-box' django validation !!
	postParams[sendingForm.elements[n].name]=sendingForm.elements[n].value;
    }

    postParams['scenarioIds'] = JSON.stringify(scenarioIds);

    RPCManager.sendRequest({
	actionURL: flooding_config.export_new_export_url,
	useSimpleHttp: true,
	httpMethod: "POST",
	params: postParams,
	callback: function(response, data, request){
	    if (response.httpResponseCode == 200) {
		console.log("Data ophalen gelukt, tonen op scherm.")
		// check if we have to open it in the pane or in the complete window
		if(data.match('redirect_in_js_to_')){
		    url = data.replace('redirect_in_js_to_/', '')
		    window.location= '/'+url;
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
    }
})

isc.DynamicForm.create({
    ID:"projectSelector",
    layoutAlign: "left",
    height: 48,
    width: 250,
    overflow:"visible",
    fields: [
	{name: "projectField",
	 optionDataSource: dsProjects,
	 type: "select",
	 emptyDisplayValue: "Selecteer project",
	 valueField:"id",
	 title: "Project",
	 showTitle: false,
	 change: "LoadScenariosForProject(value)",
	 displayField:"name"},
    ],
    autodraw: false
})


dsProjects.fetchData(null, function(response, data, request){
    if (data.length == 0){
	alert("Er zijn geen projecten waar u rechten voor hebt om ze te zien.");
    }
    else {
	projectSelector.setValueMap(data);
    }
});

/*** Create UI elements***/
isc.HTMLPane.create({
    ID: "exportRunHTMLPane",
    width:"350",
    overflow:"visible",
    border: "0px",
    contentsURL: flooding_config.root_url+"flooding/tools/export/newexport"
})

isc.ScenariosListGrid.create({
    ID:"scenariosAllListGrid",
    autodraw:false,
    canDragRecordsOut: true,
    canAcceptDroppedRecords: true,
    canReorderRecords: true,
    dragDataAction: "move",
    overflow:"visible",
    fields:[
	{name: "scenario_name", title: "Scenario naam", type: "text"},
	{name: "region_names", title: "Regio's", type: "text"},
	{name: "breach_names", title: "Doorbraak locaties", type: "text"}
    ],
    emptyMessage:"<br><br>Geen scenario's beschikbaar voor dit project."
})

isc.Img.create({
    ID:"arrowRight",
    src:"{% url root_url %}static_media/images/icons/arrow_right.png", width:32, height:32,overflow:"visible",
    click:"scenariosToExportListGrid.transferSelectedData(scenariosAllListGrid)"
})
isc.Img.create({
    ID:"arrowLeft",
    src:"{% url root_url %}static_media/images/icons/arrow_left.png", width:32, height:32,overflow:"visible",
    click:"scenariosAllListGrid.transferSelectedData(scenariosToExportListGrid)"
})

isc.ScenariosListGrid.create({
    ID:"scenariosToExportListGrid",
    canDragRecordsOut: true,
    canAcceptDroppedRecords: true,
    canReorderRecords: true,
    overflow:"visible",
    fields:[
	{name: "project_name", title: "Project naam", type: "text"},
	{name: "scenario_name", title: "Scenario naam", type: "text"},
	{name: "region_names", title: "Regio's", type: "text"},
	{name: "breach_names", title: "Doorbraak locaties", type: "text"}
    ],
    emptyMessage:"<br><br>Sleep scenario's hier heen voor export."
})

/*** Arrange UI elements ***/
isc.VLayout.create({
    overflow:"auto",
    width:"100%",
    height:"100%",
    autoDraw: true,
    membersMargin:10,
    members:[
	breadcrumbs,
	projectSelector,
	isc.HStack.create({membersMargin:10, height:160,
			   overflow:"visible",
			   members:[

			       scenariosAllListGrid,
			       isc.VStack.create({width:32, height:74, layoutAlign:"center", membersMargin:10,
					    	  members:[arrowRight,arrowLeft]}),
			       scenariosToExportListGrid
			   ]}),
	exportRunHTMLPane
    ]})  ;
