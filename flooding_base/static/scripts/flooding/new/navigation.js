/***************** functions **********************/

var newbreach_def = null;
var newselectedRegion = null;
/******************** blocks **********************/

function cancelLayerControls(){
    try {
	if (createNewMeasureAdjustEmbankmentButton.selected) {
	    createNewMeasureAdjustEmbankmentButton.deselect();
	    createNewMeasureAdjustEmbankmentButton.click();
	    polygonLayer.destroyFeatures();
	}
	if (createNewMeasureDrawEmbankmentButton.selected) {
	    createNewMeasureDrawEmbankmentButton.deselect();
	    createNewMeasureDrawEmbankmentButton.click();
	    lineLayer.destroyFeatures();
	}
    } catch (e) {
	console.log(e);
    }
}


function fnNavigation() {

    region_layers = new NOverlayContainer();

    /******************** load line and polygon drawing tools **********************/
    lineLayer = new OpenLayers.Layer.Vector("Line Layer",{displayInLayerSwitcher: false});
    polygonLayer = new OpenLayers.Layer.Vector("Polygon Layer",{displayInLayerSwitcher: false});

    lineLayer.lizard_index = 50;
    polygonLayer.lizard_index = 50;

    mainScreenManager.map.addLayers([lineLayer, polygonLayer]);

    lineLayer.setVisibility(false);
    polygonLayer.setVisibility(false);

    lineControl = new OpenLayers.Control.DrawFeature(lineLayer, OpenLayers.Handler.Path);
    polygonControl =  new OpenLayers.Control.DrawFeature(polygonLayer, OpenLayers.Handler.Polygon);
    mainScreenManager.map.addControl(lineControl);
    mainScreenManager.map.addControl(polygonControl);
    lineControl.deactivate();
    polygonControl.deactivate();


    /******************************************************************************/
    isc.DataSource.create({
    	ID:"dsListRegionMaps",
	showPrompt:false,
	dataFormat:"json",
	dataURL: locationFloodingData,
	transformRequest: function (dsRequest) {
	    if (dsRequest.operationType === "fetch") {
	        var params = {action : 'get_region_maps'};
	        // combine paging parameters with criteria
	        return isc.addProperties({}, dsRequest.data, params);
	    }
	},
	autoFetchData:false,
	autoDraw:false
    });

    fnBlockRegions = new NBlock(
        ST_REGION, ST_REGION,
	{
	    dataURL: locationFloodingData,
	    fields: [
	        {name: "rsid", primaryKey: true, hidden: true, type: "integer"},
	        {name: "rid", primaryKey:true, hidden:true, type:"integer"},
	        {name: "name", type:"text" },
	        {name: "parentid", type:"integer" ,foreignKey: "rsid", rootValue:None },
	        {name: "isregion"},
	        {name: "north" , type:"integer"},
	        {name: "south" , type:"integer"},
	        {name: "west" , type:"integer"},
	        {name: "east" , type:"integer"}
	    ],
	    transformRequest: function (dsRequest) {
	        if (dsRequest.operationType == "fetch") {
	            var params = {action : 'get_region_tree', permission:2, has_model:1};
	            // combine paging parameters with criteria
	            return isc.addProperties({}, dsRequest.data, params);
	        }
	    }
	}, {
	    emptyMessage: "<a href='javascript: fnBlockRegions.tree.fetchData()'>geen rechten voor aanmaken nieuwe scenarios</a>",
	    autoFetchData:true,
	    leafClick: function(viewer,leaf,recordNum) {

		if (leaf.isregion) {
	            set_step_one();
	            fnBlockRegions.setLabel(leaf.name);
	            newselectedRegion = leaf;//to do, dit moet anders
	            fnBlockBreaches.tree.fetchData({region_id:leaf.rid},function(dsResponse, data, dsRequest) {
	        	fnbreachLayer.refreshByData(data);
	        	fnbreachLayer.show();
	            });//teken punten via callback (na het laden)
	            Ozoom(map ,leaf );

	            region_layers.clear();
		    region_layers.addOverlays();
	            dsListRegionMaps.fetchData({region_id:leaf.rid}, function(dsResponse, data, dsRequest){
			if (data.length > 0) {
			    for (var i=0; i<data.length; i++) {
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
				region_layers.addOverlayToContainer(layer);
			    }

			    //Bestaande keringen, get_existing_embankments_shape,
			    //Hoogtekaart, action:'get_extra_grid_shapes', only_selected:True
			    //Bestaande keringen, action:'get_extra_shapes', only_selected:True
			}

		    });
	        }
	    },

	    folderClick: function(viewer,folder,recordNum){
	        Ozoom(map ,folder );
	        this.openFolder(folder);
	    }
	});


    fnBlockBreaches = new NBlock(
        ST_BREACH, ST_BREACH,
	{
	    dataURL:locationFloodingData,
	    fields:[
	        {name:"id", primaryKey:true, hidden:true, type:"integer"},
	        {name:"name", type:"text" },
	        {name:"parentid", type:"integer" ,foreignKey: "id", rootValue:None },
	        {name:"isbreach"},
	        {name:"x" , type:"integer"},
	        {name:"y" , type:"integer"}
	    ],
	    transformRequest : function (dsRequest) {
	        if (dsRequest.operationType == "fetch") {
	            var params = {action : 'get_breach_tree', permission:2, active:1};
	            // combine paging parameters with criteria
	            return isc.addProperties({}, dsRequest.data, params);
	        }
	    }
	},{
	    animateFolders:false,
	    emptyMessage: ST_SELECT_REGION,
	    leafClick: function(viewer,leaf,recordNum){
	        if (leaf.isbreach) {
		    set_step_two();
		    newbreach_def = leaf.id;//to do, dit kan anders
		    fnBlockBreaches.setLabel(leaf.name);
		    fnbreachLayer.select(leaf.id,false);
	        }
	    },
	    folderClick: function(viewer,folder,recordNum){
	        this.openFolder(folder);
	    }
	});

    isc.IButton.create({
	ID: "firstStepOk",
	title: "Ok >>",
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep2);
	},

	autoDraw: false
    });

    /*********************** step 2 *******************************/
    isc.DynamicForm.create({
	ID: "formModel",
	width: "100%",
	numCols: 2,
	overflow: "auto",
        minColWidth: 80,
	colWidths: [100, 300],
	autodraw:false,
	fields: [{
	    ID: 'selectInundationModel',
	    name: "selectInundationModel",
	    title: ST_INUNDATION_MODEL,
	    type: "select",
	    optionDataSource: isc.DataSource.create({
        	ID: "dsSelectInundationModel",
        	dataFormat: "json",
        	dataURL:locationFloodingData,
        	transformRequest : function (dsRequest) {
	            if (dsRequest.operationType == "fetch") {
	            	var params = {action : 'get_inundationmodels', only_active:true};//, onlyscenariobreaches:1
	            	// combine paging parameters with criteria
	           	return isc.addProperties({}, dsRequest.data, params);
	            }
	    	}
    	    }),
            valueField: "id",
            displayField: "name",

	    changed: function(form, item, value){
	        check_step_two();
	    }
	},{
	    ID: 'selectExtwaterModel',
	    name: "selectExtwaterModel",
	    title: ST_EXT_WATER_MODEL,
	    type: "select",
	    optionDataSource: isc.DataSource.create({
     		ID: "dsSelectExtwaterModel",
     		dataFormat: "json",
     		dataURL:locationFloodingData,
     		transformRequest : function (dsRequest) {
      		    if (dsRequest.operationType == "fetch") {
          		var params = {action : 'get_externalwatermodels', only_active:true};//, onlyscenariobreaches:1
          		// combine paging parameters with criteria
         		return isc.addProperties({}, dsRequest.data, params);
      		    }
  		}
 	    }),
            valueField: "id",
            displayField: "name",

	    changed: function(form, item, value){
	        check_step_two();
	    }
	}]
    });

    isc.IButton.create({
	ID: "secondStepBack",
	title: "<< " + ST_BACK,
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep1);
	},
	autoDraw: false
    });

    isc.IButton.create({
	ID: "secondStepOk",
	title: "Ok >>",
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep3);

	},

	autoDraw: false
    });

    /*******************third step*********************/
    isc.DataSource.create({
    	ID:"dsListLoccutoffsSet",
	showPrompt:true,
	dataFormat:"json",
	dataURL: locationFloodingData,
	transformRequest : function (dsRequest) {
	    if (dsRequest.operationType == "fetch") {
	        var params = {action : 'get_cutofflocationsets'};
	        // combine paging parameters with criteria
	        return isc.addProperties({}, dsRequest.data, params);
	    }
	},
	autoFetchData:false,
	autoDraw:false
    });

    isc.ListGrid.create({
    	ID:"listLoccutoffsSet",
    	data: [],
	width:'100%',
	height:'50%',
	margin:5,
	selectionType: "simple",
   	dataSource: dsListLoccutoffsSet,
	fields:[//project
       	    {name: "id",title: "ID",type: "number",canEdit: false,primaryKey:true,width:25,hidden:true},
       	    {name: "name",title: ST_NAME, type: "text",canEdit: false},
       	    {name: "number",title: ST_AMOUNT, type: "text",canEdit: false,width:60}
        ],
    	autoDraw:false,
    	selectionChanged: function(record, select) {

	    if (select) {
		for (var i = 0 ; i < record.cuttofflocation.length ; i++ ) {
		    fnLoccutoffsLayer.select(record.cuttofflocation[i],true);
		}
	    } else {
		for (var i = 0 ; i < record.cuttofflocation.length ; i++ ) {
		    fnLoccutoffsLayer.deselect(record.cuttofflocation[i]);
		}
	    }
    	}

    });

    isc.DataSource.create({
	ID:"dsNewLoccuttoffs",
	showPrompt:true,
	dataFormat:"json",
	dataURL: locationFloodingData,
	transformRequest : function (dsRequest) {
	    if (dsRequest.operationType == "fetch") {
	        var params = {action : 'get_cutofflocations'};
	        // combine paging parameters with criteria
	        return isc.addProperties({}, dsRequest.data, params);
	    }
	},
	transformResponse: function(dsResponse, dsRequest, data ) {
	    if (dsResponse.httpResponseCode == 200) {
	    	fnLoccutoffsLayer.refreshByData(data);
	    	fnLoccutoffsLayer.show();
	    } else {
	    	console.log('error in ophalen afsluitlocatie gegevens');
	    }
	},
	autoFetchData:false,
	autoDraw:false
    });

    isc.DataSource.create({
    	ID:"dsListLoccutoffs",
    	autoDraw:false,
	clientOnly:true,
    	fields:[
      	    {name: "id", type: "number",  primaryKey: true, hidden:true},
            {name:"type", type: "number"},
            {name: "name", type: "text"},
            {name: "action", type: "text"},
            {name: "tclose", type: "text"}
   	]
    });

    isc.ListGrid.create({
    	ID:"listLoccutoffs",
    	data: [],
	width:'100%',
	height:'100%',
	margin:5,
	canFreezeFields:true,
    	showFilterEditor:false,
    	canReorderRecords:true,
    	canGroupBy:true,
    	//canHover:true,
    	//cellPadding:5,
    	canEdit:true, editEvent:"click", editByCell: true,
	modalEditing:true,
    	alternateRecordStyles:true,
    	wrapCells: true,
    	fixedRecordHeights: false,
   	groupStartOpen:'all',
    	//groupByField: 'regions_name',
    	//showFilterEditor: true,
	fields:[
       	    //{name: "id",title: "id",type: "number",canEdit: false,primaryKey:true,width:25,hidden:true},
            {name:"type",title: ST_TYPE, type:"image",canEdit: false, width:25},
       	    {name: "name",title: ST_NAME,type: "text",canEdit: false},
       	    {name: "action",title: ST_ACTION,type: "text", valueMap:{1:"Dicht", 2:"Open"},
       	     defaultValue:1, canEdit: true,width:40, editorProperties:{width:80}},
       	    {name: "tclose",title: ST_ACTION_AFTER,type: "text",canEdit: true,formatCellValue:"intervalFormatter(intervalReader(value));",width:60}//interval editor!
        ],
    	autoDraw:false,
    	recordClick: function(viewer, record, recordNum) {  	}
    });

    isc.IButton.create({
	ID: "thirdStepBack",
	title: "<< " + ST_BACK,
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep2);

	},
	autoDraw: false
    });

    isc.IButton.create({
	ID: "thirdStepOk",
	title: "Ok >>",
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep4);
	},
	autoDraw: false
    });



    /******************* Fourth step  *********************/
    isc.DataSource.create({
	ID:"dsMeasures",
	showPrompt:true,
	dataFormat:"json",
	dataURL: locationFloodingData,
	autoFetchData:false,
	autoDraw:false
    });

    isc.ListGrid.create({
    	ID:"listMeasures",
    	data: [],
	width:'100%',
	height:'80%',
	margin:5,
	//selectionType: "simple",
   	//dataSource: dsMeasures,
   	clientOnly:true,
   	canEdit: true,
	//editEvent: "click",
	modalEditing:true,
	bodyOverflow: "visible",
	leaveScrollbarGap: false,
	fields:[//project
       	    {name: "id",title: "id",type: "number",canEdit: false,primaryKey:true,width:1, hidden:true},
       	    {name: "name",title: ST_NAME,type: "text",canEdit: true},
       	    {name: "number_embankment_units",title: ST_NR_UNITS,type: "text", canEdit: false,width:30},
       	    {name: "reference",title: ST_REFERENCE,type: "text", valueMap:{1:"tov huidige hoogte", 2:"tov NAP"},
       	     defaultValue:"tov NAP", canEdit: true,width:60, editorProperties:{width:80}},
       	    {name: "adjustment",title: ST_ADJUSTMENT,type: "float", canEdit: true,width:50}
        ],
    	autoDraw:false
    });



    isc.IButton.create({
        ID: "createNewMeasureDrawEmbankmentButton",
        title: ST_NEW_MEASURE_DRAW_EMBANKMENT,
    	showRollOver: false,
    	showDown: true,
    	showFocused: false,
    	actionType: "checkbox",
        width: "100%",
        click: function() {
            if (this.isSelected()) {
		lineControl.activate();
		lineLayer.setVisibility(true);
	        this.setTitle(ST_STOP_MODIFY);
	        createNewMeasureAdjustEmbankmentButton.disable();
	        deleteMeasureButton.disable();
	        fourthStepBack.disable();
	        fourthStepOk.disable();
	        listMeasures.disable();
	    } else {
	        //alert('save');
	        listMeasures.enable();
	        fourthStepOk.enable();
	        fourthStepBack.enable();
	        deleteMeasureButton.enable();
	        createNewMeasureAdjustEmbankmentButton.enable();
	        this.setTitle(ST_NEW_MEASURE_DRAW_EMBANKMENT);
	        lineLayer.setVisibility(false);
	        lineControl.deactivate();
	        saveDrawnEmbankment();
	    }
        },
        autoDraw: false
    });

    function saveDrawnEmbankment(){
    	lineStrings = [];
    	for(var i=0; i< lineLayer.features.length; i++){
    	    lineStrings.push(lineLayer.features[i].geometry.toString());
    	}

    	joinedLineStrings = lineStrings.join(';')
    	console.log(joinedLineStrings);

    	var	region = fnBlockRegions.tree.getSelectedRecord();

    	RPCManager.sendRequest({
	    actionURL: locationFloodingData,
	    useSimpleHttp: true,
	    showPrompt:true,
	    httpMethod: "POST",
	    params: {action: 'save_drawn_embankment', geometry: joinedLineStrings, strategy_id: strategyId, region_id: region.rid },
	    callback: function(response, data, request){
		var info = JSON.parse(data);
		if (response.httpResponseCode == 200 && info.successful == True) {
		    var info = JSON.parse(data);
		    console.log("Data ophalen gelukt, tonen op scherm.")
		    existing_embankments_layer.redraw();
		    lineLayer.destroyFeatures();

		    var record = {id:info.id,name:info.name, number_embankment_units: info.number_embankment_units, reference:2, adjustment:0};
		    listMeasures.data.addAt(record);


		} else {

		    console.log("Fout bij het ophalen van gegevens.");
		}
	    }
	});
    }

    isc.IButton.create({
        ID: "loadStrategyButton",
        title: ST_LOAD + " " + ST_MEASURES,
    	showRollOver: false,
    	showDown: true,
    	showFocused: false,
    	actionType: "checkbox",
        width: "100%",
        click: function(form, item){
	    if (typeof(loadStrategyWindow) == "undefined") {
	        console.log('create load strategy window');
	        create_load_strategy_window();
	    }

	    loadStrategyWindow.show();

	    var	region = fnBlockRegions.tree.getSelectedRecord();

	    loadStrategyContent.setContentsURL(locationFloodingData, { action:"select_strategy", region_id: region.rid }	)
	},
        autoDraw: false
    });


    isc.IButton.create({
        ID: "createNewMeasureAdjustEmbankmentButton",
        title: ST_NEW_MEASURE_EDIT_EMBANKMENT,
    	showRollOver: false,
    	showDown: true,
    	showFocused: false,
    	actionType: "checkbox",
        width: "100%",
        click: function() {

            if (this.isSelected()) {
		polygonControl.activate();
		polygonLayer.setVisibility(true);
	        this.setTitle(ST_STOP_MODIFY);
	        createNewMeasureDrawEmbankmentButton.disable();
	        deleteMeasureButton.disable();
	        fourthStepBack.disable();
	        fourthStepOk.disable();
	        listMeasures.disable();
	    } else {
	        listMeasures.enable();
	        fourthStepOk.enable();
	        fourthStepBack.enable();
	        deleteMeasureButton.enable();
	        createNewMeasureDrawEmbankmentButton.enable();
	        this.setTitle(ST_NEW_MEASURE_EDIT_EMBANKMENT);
	        polygonLayer.setVisibility(false);
	        polygonControl.deactivate();
	        selectExistingEmbankmentsByPolygon();
	    }
        },
        autoDraw: false
    });

    function selectExistingEmbankmentsByPolygon(){
    	polygonStrings = [];
    	for(var i=0; i< polygonLayer.features.length; i++){
    	    polygonStrings.push(polygonLayer.features[i].geometry.toString());
    	}

    	joinedPolygonStrings = polygonStrings.join(';')
    	console.log(joinedPolygonStrings);
    	var	region = fnBlockRegions.tree.getSelectedRecord();

    	RPCManager.sendRequest({
	    actionURL: locationFloodingData,
	    useSimpleHttp: true,
	    showPrompt:true,
	    httpMethod: "POST",
	    params: {action: 'select_existing_embankments_by_polygon', geometry: joinedPolygonStrings, strategy_id: strategyId, region_id: region.rid },
	    callback: function(response, data, request){
		var info = JSON.parse(data);
		if (response.httpResponseCode == 200 && info.successful == True ) {
		    console.log("Data ophalen gelukt, tonen op scherm.")
		    existing_embankments_layer.redraw();
		    polygonLayer.destroyFeatures();

		    var record = {id:info.id,name:info.name, number_embankment_units: info.number_embankment_units, reference:2, adjustment:0};
		    listMeasures.data.addAt(record);
		} else {
		    console.log("Fout bij het ophalen van gegevens.");
		}
	    }
	});
    }

    isc.IButton.create({
	ID: "deleteMeasureButton",
	title: ST_DELETE + " " + ST_MEASURES,
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: "100%",
	click: function(form, item){
	    var records = listMeasures.getSelection();
	    measure_ids = []
	    for (var i = 0 ; i < records.length ; i ++) {
		measure_ids.push(records[i].id)
	    }
    	    RPCManager.sendRequest({
		actionURL: locationFloodingData,
		useSimpleHttp: true,
		showPrompt:true,
		httpMethod: "POST",
		params: {action: 'delete_measure', measure_ids: measure_ids.join(';') },
		callback: function(response, data, request){
		    if (response.httpResponseCode == 200) {
			var info = JSON.parse(data);
			console.log("Data ophalen gelukt, tonen op scherm.")
			for (var i = 0; i < measure_ids.length; i++) {
			    listMeasures.data.remove(listMeasures.data.find("id",measure_ids[i]));
			}
			existing_embankments_layer.redraw();
		    }
		    else {
			alert(ST_ALERT_1);
		    }
		}
	    });

	},
	autoDraw: false
    });

    isc.IButton.create({
	ID: "fourthStepBack",
	title: "<< " + ST_BACK,
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 75,
	click: function(form, item){
	    tabSetNewScenario.selectTab(tab_fnNavigationStep3);

	},
	autoDraw: false
    });




    function create_windowsettings() {
	
    	var content = isc.HTMLPane.create({
	    ID: "settingContent",
	    width: "100%",
	    height: "100%",
	    contentsURL:"",
	    border: "none",
	    overflow:"auto",
	    autoDraw: false // Note: needed for creating the pane object with all its content
	});

	isc.Window.create({
	    ID: "windowsettings", title: ST_WIN_SETTINGS_TITLE,
	    items: [settingContent],
	    showMinimizeButton: false,
	    keepInParentRect: true,
	    showResizeBar: false,
	    closeClick: function(){
	        this.hide();
	        return false;
	    },
	    isModal: true, showShadow: true, bodyColor: "#FEFEFE",
	    height: 600, width: 800, overflow: 'hide', autoCenter: true, shadowDepth: 10,
	    autoDraw: false
	});

    }

    function create_load_strategy_window() {

    	var content = isc.HTMLPane.create({
	    ID: "loadStrategyContent",
	    width: "100%",
	    height: "100%",
	    contentsURL:"",
	    border: "none",
	    overflow:"auto",
	    autoDraw: false // Note: needed for creating the pane object with all its content
	});

	isc.Window.create({
	    ID: "loadStrategyWindow", title: ST_LOAD + " " + ST_MEASURES,
	    items: [loadStrategyContent],
	    showMinimizeButton: false,
	    keepInParentRect: true,
	    showResizeBar: false,
	    closeClick: function(){
	        this.hide();
	        return false;
	    },
	    isModal: true, showShadow: true, bodyColor: "#FEFEFE",
	    height: 600, width: 400, overflow: 'hide', autoCenter: true, shadowDepth: 10,
	    autoDraw: false
	});

    }

    isc.IButton.create({
	ID: "fourthStepOk",
	title: ST_CONF_AND_SAVE_TITLE,
	showRollOver: false,
	showDown: true,
	showFocused: false,
	width: 180,
	click: function(form, item){
	    var is_3di, action;
	    if (typeof(windowsettings) == "undefined") {
	        console.log('create windowsettings');
	        create_windowsettings();
	    }

	    is_3di = formModel.getItem("selectInundationModel").getSelectedRecord().is_3di;
	    action = "compose_scenario";
	    if (is_3di) {
		action = "compose_3di_scenario";
	    }
	    windowsettings.show();
	    var breach = fnBlockBreaches.tree.getSelectedRecord();
	    settingContent.setContentsURL(locationFloodingData, { action: action, breach_id: breach.id }	)
	},

	autoDraw: false
    });

    /******************** screen **********************/
    function set_step_one() {
	tabSetNewScenario.disableTab('tab_fnNavigationStep2');
	tabSetNewScenario.disableTab('tab_fnNavigationStep3');
	tabSetNewScenario.disableTab('tab_fnNavigationStep4');
	firstStepOk.setDisabled(true);
    }

    function set_step_two() {
	tabSetNewScenario.enableTab('tab_fnNavigationStep2');
	tabSetNewScenario.disableTab('tab_fnNavigationStep3');
	tabSetNewScenario.disableTab('tab_fnNavigationStep4');
	firstStepOk.setDisabled(false);
	secondStepOk.setDisabled(true);
    }

    function set_step_three() {
	tabSetNewScenario.enableTab('tab_fnNavigationStep3');
	tabSetNewScenario.enableTab('tab_fnNavigationStep4');
	secondStepOk.setDisabled(false);

    }

    function set_step_four() {
	tabSetNewScenario.enableTab('tab_fnNavigationStep4');
    }

    function check_step_one() {

    }

    function check_step_two() {
	//to do: add check
	if (selectInundationModel.getSelectedRecord() &&
            (selectExtwaterModel.isDisabled() ||
             selectExtwaterModel.getSelectedRecord())) {
	    set_step_three();
	}
    }

    step2_last_region = null;
    step2_last_extw = null;

    function fetch_step_two() {
	var region = fnBlockRegions.tree.getSelectedRecord();
	var breach = fnBlockBreaches.tree.getSelectedRecord();
	var extw = fnBlockBreaches.tree.data.findById(breach.parentid);

	if (step2_last_region != region.rid) {
	    if (typeof(strategyId)!='undefined') {
		delete strategyId ;
	    }
	    step2_last_region = region.rid;
	    selectInundationModel.resetValue();
	    selectInundationModel.fetchData(function(item, DSResponse){
		if(DSResponse.data.length == 1) {
		    item.setValue(DSResponse.data[0].id);
		    check_step_two();
		}
	    },
			                    {data:{region_id: region.rid}});
	}

	if (step2_last_extw != extw.id) {
	    step2_last_extw = extw.id;
	    selectExtwaterModel.resetValue();
	    if (extw.type == 3) {
		selectExtwaterModel.fetchData(function() {check_step_two() }, {data: {breach_id: breach.id}});
		selectExtwaterModel.enable();
	    } else {
		selectExtwaterModel.disable();
	    }
	}
	check_step_two();
    }

    step3_last_inundationmodel = null;
    step3_last_extwatermodel = null;

    function fetch_step_three() {
	var inundationmodel = selectInundationModel.getSelectedRecord();
	var extwatermodel = selectExtwaterModel.getSelectedRecord();
	if (extwatermodel == null) {
	    extwatermodel = {id: null};
	}
	if ((step3_last_inundationmodel != inundationmodel.id)|| (step3_last_extwatermodel!= extwatermodel.id)) {
	    step3_last_inundationmodel = inundationmodel.id;
	    step3_last_extwatermodel = extwatermodel.id;

	    listLoccutoffs.setData([]);
	    var arguments = { inundationmodel_id: inundationmodel.id }
	    if (extwatermodel.id != null) {
		arguments['extwatermodel_id'] = extwatermodel.id
	    }
	    listLoccutoffsSet.fetchData(arguments);
	    dsNewLoccuttoffs.fetchData(arguments);

	}
    }

    step4_last_region = null;


    function fetch_step_four() {


	var region= fnBlockRegions.tree.getSelectedRecord();

	if (step4_last_region != region.rid) {
	    delete(strategyId);

	    while (listMeasures.data.remove(listMeasures.data[0]) == True) {
		//pass
	    }


	    step4_last_region = region.rid;
	}

	if (typeof(strategyId)=='undefined') {
    	    RPCManager.sendRequest({
		actionURL: locationFloodingData,
		useSimpleHttp: true,
		httpMethod: "GET",
		params: {action: 'get_strategy_id' },
		callback: function(response, data, request){
		    if (response.httpResponseCode == 200) {
			var info = JSON.parse(data);
			console.log("Data ophalen gelukt, tonen op scherm.")
			tabSetNewScenario.selectTab(tab_fnNavigationStep4);
			strategyId = info.strategyId
			existing_embankments_layer.setParams({strategy_id:strategyId});
			var	region = fnBlockRegions.tree.getSelectedRecord();
			existing_embankments_layer.setParams({region_id: region.rid, strategy_id: strategyId});
			existing_embankments_layer.show();

			//alert(strategyId);
		    } else {
			console.log("Fout bij het ophalen van gegevens.");
		    }
		}
	    });

	} else {
	    existing_embankments_layer.show();
	}
    }

    isc.VLayout.create({
	ID:"fnNavigationStep1",
	membersMargin: 5,
	width: "100%", height: "100%", overflow:"hidden",
	members: [
	    isc.VLayout.create({ height:"25%", members: fnBlockRegions.getMembers(),    autoDraw:false}),
	    isc.VLayout.create({ height:"20%", members: fnBlockBreaches.getMembers(),   autoDraw:false}),
	    isc.HLayout.create({ height:"30", members: [isc.Canvas.create({ width:"*", autoDraw:false}), firstStepOk],   autoDraw:false})
	],
	autoDraw:false
    });

    isc.VLayout.create({
	ID:"fnNavigationStep2",
	membersMargin: 5,
	width: "100%", height: "100%", overflow:"hidden",
	members: [
	    formModel,
	    isc.Canvas.create({ height:"*", members: [],   autoDraw:false}),
	    isc.HLayout.create({ height:"30", members: [secondStepBack, isc.Canvas.create({ width:"*", autoDraw:false}),secondStepOk],   autoDraw:false})
	],
	autoDraw:false
    });



    isc.VLayout.create({
	ID:"fnNavigationStep3",
	membersMargin: 5,
	width: "100%", height: "100%", overflow:"hidden",
	members: [
	    isc.Label.create({height: 24, overflow:"hidden", align: "left", top:5, wrap: false, showEdges: false, contents: "<h3>" + ST_LOCATION_SET + "</h3>"}),
	    listLoccutoffsSet,
	    isc.Label.create({height: 24, overflow:"hidden", align: "left", top:5, wrap: false, showEdges: false, contents: "<h3>" +ST_SELECTED_CUTOFF_LOC + "</h3>"}),
	    listLoccutoffs,
	    isc.Canvas.create({ height:"*", members: [],   autoDraw:false}),
	    isc.HLayout.create({ height:"30", members: [thirdStepBack, isc.Canvas.create({ width:"*", autoDraw:false}),thirdStepOk],   autoDraw:false})
	],
	autoDraw:false
    });


    isc.VLayout.create({
	ID:"fnNavigationStep4",
	membersMargin: 5,
	width: "100%", height: "100%", overflow:"hidden",
	members: [
	    isc.Label.create({height: 34, overflow:"hidden", align: "left", top:5, wrap: false, showEdges: false, contents: "<h3>" + ST_MEASURES + "</h3>"}),
	    listMeasures,
	    isc.VLayout.create({height:"90",
	   			members: [ loadStrategyButton, createNewMeasureDrawEmbankmentButton, createNewMeasureAdjustEmbankmentButton, deleteMeasureButton],
	   			autoDraw:false
	   		       }),
	    isc.Canvas.create({ height:"*", members: [],   autoDraw:false}),
	    isc.HLayout.create({ height:"30", members: [fourthStepBack, isc.Canvas.create({ width:"*", autoDraw:false}),fourthStepOk],   autoDraw:false})
	],
	autoDraw:false
    });



    isc.TabSet.create({
        ID:"tabSetNewScenario",
        tabBarPosition: "bottom",
        destroyPanes:"false",
        symmetricEdges:false,
        tabs:[
            {title:ST_STEP + '1', ID:"tab_fnNavigationStep1", pane: 'fnNavigationStep1'},
            {title:ST_STEP + '2', ID:"tab_fnNavigationStep2", pane: 'fnNavigationStep2'},
            {title:ST_STEP + '3', ID:"tab_fnNavigationStep3", pane: 'fnNavigationStep3'},
            {title:ST_STEP + '4', ID:"tab_fnNavigationStep4", pane: 'fnNavigationStep4'}
        ],
        tabSelected: function(tabNum, tabPane, ID, tab) {
            if (ID == "tab_fnNavigationStep1") {
        	//set_step_one();//only first time
        	check_step_one();
        	if (typeof(fnbreachLayer) != 'undefined') {
        	    fnbreachLayer.show();
        	}
            }
            else if (ID == "tab_fnNavigationStep2") {
        	fetch_step_two();
        	check_step_two();
            }
            else if (ID == "tab_fnNavigationStep3") {
        	fetch_step_three();
		fnLoccutoffsLayer.show();
            }
            else if (ID == "tab_fnNavigationStep4") {
        	fetch_step_four();

            }

        },
        tabDeselected: function(tabNum, tabPane, ID, tab) {
            if (ID == "tab_fnNavigationStep1") {
		fnbreachLayer.hide();
            }
            else if (ID == "tab_fnNavigationStep2") {

            }
            else if (ID == "tab_fnNavigationStep3") {
        	fnLoccutoffsLayer.hide();
            }
            else if (ID == "tab_fnNavigationStep4") {
		cancelLayerControls();
		existing_embankments_layer.hide();
		lineLayer.setVisibility(false);
    		polygonLayer.setVisibility(false);

            }

        },
        width:'100%', height:'100%',
        backgroundColor:"white", //opacity:100,
        paneContainerOverflow:"hidden",
        autoDraw:false
    });

    //this.tabSet.addTab({title:infoWindows[i].tabName, ID:("tab_"+infoWindows[i].id), pane: infoWindows[i].pane, disabled:!infoWindows[i].enabled});

    return tabSetNewScenario;
}



