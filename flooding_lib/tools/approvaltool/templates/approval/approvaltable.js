
isc.DataSource.create({
    ID:"dsPostApproval",
    dataFormat:"json",
    dataURL: '{{ post_url }}',
    requestProperties: { httpMethod: "POST" },
    autoDraw:false
});

isc.ListGrid.create({
    ID: "approvalList",
    width:380, alternateRecordStyles:true, cellHeight:22, wrapCells: true, fixedRecordHeights: false,

    fields:[
        {name:"successful", title:"Status", width:60, type:"image",valueMap:["true", "false", "-"], imageURLPrefix:"{% url "root_url" %}static_media/images/", imageURLSuffix:".gif", canEdit:true},
        {name:"name", title: "Controle", width: 120, showHover: true, canEdit:false, hoverHTML:"return record.description"},
        {name:"creatorlog",title: "Door", width:70, canEdit:false,showHover: true,hoverHTML:"return record.date"},
        {name:"remarks", title: "Keurings opmerkingen", editorProperties:{height:60}}
    ],
    data:

    {{ lines|safe }}{% ifequal forloop.last 0 %},{% endifequal %}

    ,

    canEdit: true,
    editEvent: "click",
    modalEditing:true,
    bodyOverflow: "visible",
    overflow: "visible",
    leaveScrollbarGap: false,
    hoverWidth:300,
    autodraw:false
})

isc.IButton.create({
    ID: "buttonApprovalSave",
    title: "Keuring opslaan",
    showRollOver: false,
    showDown: true,
    showFocused: false,
    width: 150,

    showRollOver: false,
    click: function() {
        var newdata = approvalList.getData();
        var send = {}
        for (var i = 0 ; i < newdata.length ; i++) {
            send[newdata[i].id] = '{"name": "'+newdata[i].name+'", "successful": "'+newdata[i].successful+'", "remarks": "'+newdata[i].remarks+'","creatorlog":"'+newdata[i].creatorlog+'"}'
        }

        dsPostApproval.fetchData(send, function(dsResponse, data, dsRequest) {
            if (dsResponse.httpResponseCode == 200) {
                if (data[0]["lines"]) {
                    approvalList.setData(data[0]["lines"]);
                }

            }
        });
    },
    autoDraw: false
});


isc.HLayout.create({
    ID: 'approvalButtons',
    height: 28,
    padding: 2,
    membersMargin: 5,
    backgroundColor: 'grey',
    overflow: "visible",
    border: "1px solid grey",
    resizeBarTarget: "next",
    members: [
        buttonApprovalSave
    ],
    autoDraw: false
});



isc.VLayout.create({
    ID: 'scApprovalTotal',
    width: "100%",
    height:"100%",
    overflow: "auto",
    members: [
        approvalList,
        approvalButtons
    ],
    autoDraw: false
});