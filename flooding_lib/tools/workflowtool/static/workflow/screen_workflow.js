console.log('loading screaan_exports ..');

/********************************************************************/
/**** script: 		screen_exports
/**** description: 	This script provides the functionaly to export 
                        'waterdieptekaart'
/********************************************************************/

isc.Canvas.create({
    ID:'breadcrumbs',
    height:"24",
    contents: wConfig.breadcrumbs,
    autodraw:false
});

var createPagingButton = function(idButton, titleButton, widthButton, isDisabled) {
    return isc.Button.create({
	ID: idButton,
	//autoFit: true,
	autoDraw: false,
	align: "center",
	disabled: isDisabled,
	width: widthButton,
	title: titleButton,
	click : function () {
        // have buttons exchange their titles
            var title1 = but1.getTitle();
            but1.setTitle(but2.getTitle());
            but2.setTitle(title1);
	}
    });
};

isc.ImgButton.create({
    ID: "butStart",
    size: 24,
    prompt: "Start geselecteerde scenario(s)",
    vAlign: "center",
    src: wConfig.icons_url + "workflow_start.png",
    click: function() {
	var selectedRows = workflowScenariosListGrid.getSelection();
	var postParams = [];
	var scenarios = [];
	for (var i = 0; i < selectedRows.length; i++){
    	    scenarios[i] = {"scenario_id": selectedRows[i].scenario_id,
			    "template_id": selectedRows[i].template_id}
	}
	postParams['scenarios'] = JSON.stringify(scenarios);
	RPCManager.sendRequest({
	    actionURL: wConfig.startscenarios_url,
	    useSimpleHttp: true,
	    httpMethod: "POST",
	    params: postParams,
	    callback: function(response, data, request){
		if (response.httpResponseCode == 200) {
		    console.log("Data ophalen gelukt, tonen op scherm.");
		} else {
		    console.log("Fout bij het ophalen van gegevens.");
		}
	    }
	});
    }
});

isc.ImgButton.create({
    ID: "butRefresh",
    size: 24,
    prompt: "Reload",
    vAlign: "center",
    showRollOver: false,
    showFocused: false,
    src: wConfig.icons_url + "workflow_refresh.png",
    click: function() {
	workflowScenariosListGrid.destroy();
	ScenarioVLayout.addMember(createWorkflowScenariosListGrid(),1);
    }
});

var createPagingStack = function() {
    var pagingStack = []
    pagingStack[0] = createPagingButton("butPrev", "<", 20, true);
    for (var i = 1; i < 10; i++) {
	pagingStack[i] = createPagingButton("but" + i, i, 20, false);
    }
    pagingStack[11] = createPagingButton("butNext", ">", 20, false);
    pagingStack[12] = createPagingButton("butInfo", "..", 80, true);
    return pagingStack;
};

/*** DATASOURCES ***/
  
isc.DataSource.create({
    ID: "dsScenario",
    showPrompt: false,
    dataFormat: "json",
    dataURL: wConfig.scenarios_processing_url,
    transformRequest: function (dsRequest) {	
	if (dsRequest.operationType == "fetch") {
	    var params = {};
	    for (var n = 0; n < toolsForm.items.length; n++){
		params[toolsForm.items[n].name] = toolsForm.items[n].getValue();
	    }
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    fields:[
	{name:"execute_url", hidden:false, type:"text"},
	{name:"scenario_id", primaryKey:true, hidden:false, type:"int"},
	{name:"scenario_name", hidden: false, type:"text"},
	{name:"template_id", hidden: true, type:"int"},
	{name:"template_code", hidden: false, type:"text"},
	{name:"workflow_status", hidden: false, type:"text"},
	{name:"breach", hidden: false, type:"text"},
	{name:"region", hidden: false, type:"text"},
	{name:"project_id", hidden: true, type:"int"},
	{name:"project_name", hidden: false, type:"text"},
	{name:"workflows_count", hidden: false, type:"int"},
	{name:"workflow_created", hidden: false, type:"text"},
	{name:"workflow_tfinished", hidden: false, type:"text"}
    ]
});

isc.ResultSet.create({
    dataSource : "dsScenario"
});

isc.DataSource.create({
    ID: "dsWorkflowTask",
    showPrompt: false,
    dataFormat: "json",
    dataURL: wConfig.workflow_task_url,
    recordXPath:"results",
    transformRequest: function (dsRequest) {	
	if (dsRequest.operationType == "fetch") {
	    var params = {};
	    // for (var n = 0; n < toolsForm.items.length; n++){
	    // 	params[toolsForm.items[n].name] = toolsForm.items[n].getValue();
	    // }
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    fields:[
	{name:"execute_url", hidden:false, type:"text"},
	{name:"workflow", primaryKey:true, hidden:false, type:"int"},
	{name:"code", hidden: false, type:"text"},
	{name:"tcreated", hidden: false, type:"text"},
	{name:"tqueued", hidden: false, type:"text"},
	{name:"tstart", hidden: false, type:"text"},
	{name:"tfinish", hidden: true, type:"int"},
	{name:"status", hidden: false, type:"text"}
    ]
});

isc.ResultSet.create({
    dataSource : "dsWorkflowTask"
});

isc.DataSource.create({
    ID: "dsWorkflowContext",
    dataFormat: "json",
    dataURL: wConfig.last_pagenumber_url,
    fields:[
	{name:"last_pagenumber", type:"int"}
    ]
});

// isc.ResultSet.create({
//     dataSource : "dsWorkflowContext"
// });


var LoadLastPageNumber = function(){
    dsWorkflowContext.transformRequest= function (dsRequest) {
    	if (dsRequest.operationType == "fetch") {
    	    var params = {};
    	    return isc.addProperties({}, dsRequest.data, params);
    	}
    };

    dsWorkflowContext.fetchData({}, function(response, data, request){
	if (data.length > 0) {
	    wConfig.last_pagenumber = data[0].last_pagenumber;
	    butPrev.setVisibility(false);
	    butInfo.setTitle("Page 1 of " + data[0].last_pagenumber);
	}
    });  
};

/*** SPECIAL SCENARIO LISTGRID CLASS ***/
isc.defineClass("ScenariosListGrid", "ListGrid").addProperties({
    width: "100%",
    height: "80%",
    cellHeight:24,
    //imageSize:16,
    border:"1px solid gray",
    //bodyStyleName:"normal",
    loadingDataMessage: "Data aan het laden...",
    //alternateRecordStyles:true,
    showHeader:true,
    leaveScrollbarGap:false
});

var createWorkflowScenariosListGrid = function() {

    var g = isc.ScenariosListGrid.create({
	ID:"workflowScenariosListGrid",
	alternateRecordStyles:true,
	baseStyle: "myBoxedGridCell",
	autoDraw:false,
	canReorderRecords: true,
	overflow:"visible",
	dataSource: dsScenario,
	useClientFiltering: false,
	useClientSorting: false,
	showFilterEditor:true,
	autoFetchData: true,
	fields:[
	    {name:"execute_url", title:"Start", width:50, 
	     type:"link", align:"center", canFilter:false, canSort:false,
	     linkText:isc.Canvas.imgHTML(wConfig.images_url + "navPlay.png",20,20)},
	    {name:"scenario_id", title:"ID", type:"int", width:40},
	    {name:"scenario_name", title: "Scenario", type: "text", formatCellValue: function (value, record) {
		    if (value) {
			return "<a target='_new' title='Open scenario' href='" + wConfig.scenario_url + record.project_id + "/" + record.scenario_id + "/'>" +
			    value + "</a>";
		    }
		}
	    },
	    {name:"template_id", "showIf": "false", type:"int"},
	    {name:"template_code",title:"Template", type:"text", width: 55, align: "center"},
	    {name:"workflow_status", title:"Status", type:"text", width: 60, formatCellValue:"isc.Format.toUSString(value)"},
	    {name:"breach", title:"Bres", type:"text"},
	    {name:"region", title:"Regio", type:"text"},
	    {name:"project_id", title:"Project id", showIf: "false", type:"int"},
	    {name:"project_name", title:"Project", type:"text"},
	    {name:"workflows_count", title:"Uitvoeringen", type:"int", width: 55, align: "center"},
	    {name:"workflow_created", title:"Aangemaakt op", type:"text", width: 120},
	    {name:"workflow_tfinished", title:"Finished op", type:"text", width: 120}
	],
	emptyMessage:"<br><br>Geen scenario's.",
	getCellCSSText: function (record, rowNum, colNum) {
	    if (this.getFieldName(colNum) == "workflow_status") {
		if (record.workflow_status == 'SUCCESS') {
		    return "font-weight:bold; color:green;";
		} else if (record.workflow_status == 'FAILED') {
		    return "font-weight:bold; color:red;";
		}
	    }
	}
	// formatCellValue: function (value, record, rowNum, colNum) {
	// 	debugger;
	// 	var field = this.getField(colNum);
	//     if (!field.hasLink) {
	// 	    return value;
	// 	}
	//     return "<a href='javascript:void(0)' onclick='doLink(\"" + this.ID + "\"," + rowNum + "," + colNum + ")'>" + value + "</a>";
	// }
    });

    return g;
};

var createWorkflowsTaskListGrid = function() {

    var g = isc.ScenariosListGrid.create({
	ID:"workflowTasksListGrid",
	alternateRecordStyles:true,
	baseStyle: "myBoxedGridCell",
	autoDraw:false,
	canReorderRecords: true,
	overflow:"visible",
	dataSource: dsWorkflowTask,
	useClientFiltering: false,
	useClientSorting: false,
	showFilterEditor:true,
	autoFetchData: true,
	fields:[
	    {name:"execute_url", title:"Start", width:50, type:"link", 
	     align:"center", canFilter:false, canSort:false,
	     linkText:isc.Canvas.imgHTML(wConfig.images_url + "navPlay.png",20,20)},
	    {name:"workflow", title:"Workflow ID", type:"int", width:40,
	    getGroupTitle: function (groupValue, groupNode, field, fieldName, grid) {
		baseTitle = groupValue + "<a>Start workflow</a>";
		return baseTitle;
	    }
	    },
	    {name:"code",title:"Code", type:"text", width: 55, align: "center"},
	    {name:"tcreated", title:"created", type:"text"},
	    {name:"tqueued", title:"queued", type:"text", showIf: "false"},
	    {name:"tstart", title:"started", type:"text", showIf: "false"},
	    {name:"tfinish", title:"finished", type:"text"},
	    {name:"status", title:"Status", type:"int", width: 55,
	     align: "center", formatCellValue:"isc.Format.toUSString(value)"}
	],	
	groupStartOpen:"first",
	groupByField: 'workflow',
	emptyMessage:"<br><br>Geen scenario's.",
	getCellCSSText: function (record, rowNum, colNum) {
	    if (this.getFieldName(colNum) == "status") {
		if (record.status == 'SUCCESS') {
		    return "font-weight:bold; color:green;";
		} else if (record.status == 'FAILED') {
		    return "font-weight:bold; color:red;";
		}
	    }
	}
	// formatCellValue: function (value, record, rowNum, colNum) {
	// 	debugger;
	// 	var field = this.getField(colNum);
	//     if (!field.hasLink) {
	// 	    return value;
	// 	}
	//     return "<a href='javascript:void(0)' onclick='doLink(\"" + this.ID + "\"," + rowNum + "," + colNum + ")'>" + value + "</a>";
	// }
    });

    return g;
};


isc.DataSource.create({
    ID: "dsRowsToLoad",
    showPrompt: false,
    dataFormat: "json",
    dataURL: wConfig.rowstoload_url,
    transformRequest: function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {};
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    fields:[
	{name:"name", hidden:true, type:"text"},
	{name:"val", hidden: false, type:"int"}
    ]
});

isc.DynamicForm.create({
    ID:"toolsForm",
    height: 18,
    fields: [{ name: "rowstoload",
	       width: 100,
	       optionDataSource: dsRowsToLoad,
	       type: "select",
	       emptyDisplayValue: "Rows to load",
	       defaultValue: 25,
	       showTitle: false,
	       valueField:"val",
	       displayField:"name"},
	     {name: "scenario_id",
	      prompt:'Filter op ID (scenario_id), b.v. 200,100-120,13333',
	      width: 150,
	      type: "int",
	      emptyDisplayValue: "Scenario ID",
	      showTitle: false}
	   ]
});


LoadLastPageNumber();

isc.ToolStrip.create({
    ID: "ToolBox",
    members: [butStart, butRefresh, toolsForm]
});


/*** Arrange UI elements ***/
isc.VLayout.create({
    ID: "ScenarioVLayout",
    width: "100%",
    height: "100%",
    autoDraw: true,
    membersMargin: 0,
    members: [
	isc.HStack.create({
	    ID: "toolStack",
	    //align: "right",
	    width: "100%",
	    height: 18,
	    membersMargin: 10,
	    backgroundColor:"lightGrey",
	    border: "1px solid grey",
	    members: [butStart, butRefresh, toolsForm]
	}),
	// toolBox,
	createWorkflowScenariosListGrid(),
	//createWorkflowsTaskListGrid(),
	isc.HStack.create({
	    ID: "pagingStack",
	    overflow: "visible",
	    width: 150,
	    //membersMargin: 20,
	    height: 24,
	    layoutAlign: "center",
	    border: "1px solid blue",
	    members: createPagingStack()
	})
    ]
});