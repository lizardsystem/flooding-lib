console.log('loading screaan_exports ..');

/********************************************************************/
/**** script: 		screen_exports
/**** description: 	This script provides the functionaly to export 
                        'waterdieptekaart'
/********************************************************************/

isc.Canvas.create({
    ID:'breadcrumbs',
    height:"15",
    contents: ror_config.breadcrumbs,
    autodraw:false
});

isc.ValuesManager.create({
        ID: "vm"        
});

isc.DataSource.create({
    ID: "dsTypeKering",
    showPrompt: false,
    dataFormat: "json",
    dataURL: locationFloodingData,
    transformRequest: function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {action : 'get_ror_keringen_types'};
	    // combine paging parameters with criteria
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    autoFetchData:true,
    fields:[
    	{name:"type", hidden: false, type:"text"}
    ]
});

isc.DataSource.create({
    ID: "dsRORKeringen",
    showPrompt: false,
    dataFormat: "json",
    dataURL: locationFloodingData,
    transformRequest: function (dsRequest) {
	if (dsRequest.operationType == "fetch") {
	    var params = {action : 'get_ror_keringen'};
	    // combine paging parameters with criteria
	    return isc.addProperties({}, dsRequest.data, params);
	}
    },
    transformResponse: function(dsRequest, dsResponse, jsonData) {
	//alert('');
    },
    //autoFetchData:true,
    autoDraw:false,
    //clientOnly: false,
    fields:[
	{name: "id", primaryKey: true, hidden: true, type: "int"},
	{name: "title", hidden: false, type: "text", required: true},
	{name: "uploaded_at", hidden: true, type: "text"},
	{name: "owner", hidden: false, type: "text"},
	{name: "file_name", hidden: true, type: "text"},
	{name: "status", hidden: true, type:"text"},
	{name: "type_kering", hidden: true, type:"text"},
	{name: "type", hidden: true, type:"text", required: true},
	{name: "zip", hidden: true, type:"text", required: true},
	{name: "action", hidden: true, type:"text", required: true}
    ]
});
    
isc.ListGrid.create({
    ID: "listGridKering",
    width:650, height:224, alternateRecordStyles:true,
    dataSource: dsRORKeringen,
    selectionType: "simple",
    autoFetchData: true,
    fields:[
	{name: "id", title:"ID", type:"int", width: 20},
	{name: "title", title: "Titel", type: "text", width: 100},
	{name: "uploaded_at", title: "Geüpload op", type: "text",width: 120},
	{name:"owner", title: "Eigenaar", type:"text", width: 100},
	{name:"file_name", title: "Bestandnaam", type:"text", width: 100},
	{name:"status", title: "Status", type:"text", width: 100},
	{name:"type_kering", title: "Type", type:"text", width: 100}
    ],
    emptyMessage:"<br><br>Geen shape is beschikbaar."
});

isc.IButton.create({
    ID: "btUpload",
    title: "Upload",
    autoFit: true,
    icon: ror_config.root_url + "static_media/Isomorphic_NenS_skin/images/actions/upload.png",
    radioGroup: "views",
    actionType: "checkbox",
    click : function () {
	uploadWindow.show(); 
	uploadFrame.hide();
	uploadForm.reset()
    } 
});

isc.IButton.create({
    ID: "btSubmit",
    title: "Submit",
    autoFit: true,
    click : function () {
	var val = uploadForm.validate();
	if (val) {
	    uploadForm.submit();
	    uploadFrame.show();
	} else {
	    console.log("Error on submit.");
    	}
    }
});

isc.IButton.create({
    ID: "btClose",
    title: "Close",
    autoFit: true,
    click : function () { uploadWindow.hide(); }
});

isc.DynamicForm.create({
    ID: "uploadForm",
    dataSource: dsRORKeringen,
    action: locationFloodingData,
    target: "uploadFrame",
    dataFormat: "multipart/form-data",
    method: "POST",
    autoDraw: false,
    fields: [
	{ name: "title", required: true },
	{ name: "type", required: true, editorType: "select",
	  optionDataSource: "dsTypeKering"},
	{ name: "zip", type: "upload", required: true  },
	{ name: "action", type: "hidden", defaultValue: "upload_ror_keringen" }
    ],
    canSubmit: true
});

isc.Canvas.create({
    ID:'uploadFrame',
    height: 20,
    contents: "<iframe height=20 scrolling='no' name='uploadFrame' width='100'" +
              "align='top' border='0' frameborder='0' allowtransparency='true'>AAA</iframe>",
    autodraw: false,
    autoFit: true,
});

isc.HLayout.create({
    ID: "uploadWindowButtons",
    membersMargin: 5,
    padding: 5,
    height: 20,
    members: [btSubmit, btClose, uploadFrame]
});

isc.Window.create({
    ID: "uploadWindow",
    title: "Upload kering",
    autoSize:true,
    autoCenter: true,
    isModal: true,
    showModalMask: true,
    autoDraw: false,
    width: 400,
    closeClick : function () { 
	dsRORKeringen.fetchData({}, function(response, data, request){
	    listGridKering.setData(data);
	});
	this.Super("closeClick", arguments)
    },
    items: [
	uploadForm,	
	uploadWindowButtons
    ]
});

isc.HLayout.create({
    ID: "buttons",
    width: 500,
    membersMargin: 5,
    padding: 5,
    members: [btUpload]
});

isc.VLayout.create({
    ID: "mainLayout",
    width: 700,
    membersMargin: 10,
    members: [breadcrumbs, listGridKering, buttons]
});

var downloadButtons = function() {
    var dButtons = new Array();
    for (var i=0; i < ror_files.length; i++) {
	var fileName = ror_files[i].name;
	var path = ror_files[i].path;
	console.log(i + " " + fileName);
 	dButtons[i] = isc.IButton.create({
	    ID: fileName.split(".")[0] + i,
	    title: "Download " + fileName.split(".")[0],
	    path: path,
	    autoFit: true,
	    icon: isomorphicDir + "skins/SmartClient/images/actions/download.png",
	    radioGroup: "views",
	    actionType: "checkbox",
	    click: 'console.log("PATH: " + this.path); window.open(this.path, "uploadFrame");'
	});
    }
    return dButtons;
}

buttons.addMembers(downloadButtons());