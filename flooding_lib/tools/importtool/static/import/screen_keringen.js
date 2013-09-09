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

// var initialCriteria = {
//         _constructor:"AdvancedCriteria",
//         operator:"and",
//         criteria:[
//             { fieldName:"description", operator:"notNull" }
//         ]
//     };

isc.DataSource.create({
    ID: "dsRORKeringen",
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
    //autoFetchData:true,
    autoDraw:false,
    //clientOnly: false,
    fields:[
	{name:"id", hidden:false, type:"int"},
	{name:"title", hidden:false, type:"text"},
	{name:"created_at", hidden: false, type:"text"},
	{name:"owner_name", hidden: false, type:"text"},
	{name:"url", hidden: false, type:"text"}
    ]
});
    
isc.ListGrid.create({
    ID: "listGridSuppyItem",
    width:500, height:224, alternateRecordStyles:true,
    dataSource: dsRORKeringen,
    selectionType: "simple"
});

// isc.DynamicForm.create({
//     ID: "formDownload",
//     fields: [
//         {name:"checkbox", title:"Download to new window", type:"checkbox"}
//     ]
// });

// sc.Button.create({
//     ID: "buttonDownload",
//     width:200,
//     title: "Download Descriptions",
//     click: function () { 
//             var selectedRecords = listGridSuppyItem.getSelectedRecords();
//             if (selectedRecords.length == 0) {
//                 isc.say("You must select at least one record");
//                 return;
//             }
//              var criteria = { itemID: selectedRecords.getProperty("itemID") };
//              var dsRequest = {
//                     ID: "dsRequest",
//                     operationId: "downloadDescriptions",
//                     downloadResult: true,
//                     downloadToNewWindow: !!formDownload.getValue('checkbox')
//                };
//             //supplyItemDownload.fetchData(criteria, null, dsRequest);
//     } 
// });

isc.DynamicForm.create({
    ID: "uploadForm",
    //dataSource: mediaLibrary,
    fields: [
        { name: "title", required: true },
        { name: "zip", type: "upload", hint: "Maximum file-size is 50k", required: true },
        { title: "Save", type: "button", 
            click: function () {
                //this.form.saveData("if(dsResponse.status>=0) uploadForm.editNewRecord()");
		//listGridSuppyItem.
		var testData = [{
		    "id": 0, 
		    "title": uploadForm.getValue('title'),
		    "created_at": "nu",
		    "owner_name": "ik",
		    "url": uploadForm.getValue('zip')
		}];
		gridData = listGridSuppyItem.data;
		gridData.add(testData[0]);
		listGridSuppyItem.setData(gridData);
		listGridSuppyItem.redraw();
		
            }
        }
    ]
});

// isc.HLayout.create({
//     ID: "hLayout",
//     width: 300,
//     members: [buttonDownload, formDownload]
// });

isc.VLayout.create({
    ID: "vLayout",
    width: 300,
    members: [breadcrumbs, listGridSuppyItem, uploadForm]
});

//listGridSuppyItem.fetchData(initialCriteria);