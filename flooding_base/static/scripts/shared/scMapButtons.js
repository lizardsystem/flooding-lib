/***************mapbuttons**********/

var doneWarningIE = false;

if (!isc.Browser.isIE) {
    doneWarningIE = true;
}


function scFuncMapButtons() {


isc.IButton.create({
    ID: "buttonGraph",
    title: "Grafiek",
    showRollOver: false,
    showDown: true,
    showFocused: false,
    actionType: "radio",
    radioGroup: "typeInfo",
    width: 120,
    click: function(form, item){
        fcm.refreshContent();
    },

    autoDraw: false
});

isc.IButton.create({
    ID: "buttonTable",
    title: "Tabel",
    showRollOver: false,
    showDown: true,
    showFocused: false,
    actionType: "radio",
    radioGroup: "typeInfo",
    width: 120,
    click: function(form, item){
        fcm.refreshContent();
    },

    autoDraw: false
});



isc.ToolStrip.create({
    ID:"tsFews",
    width: 140,
    members: [
                buttonGraph,
                buttonTable],
    autoDraw:false
});

buttonGraph.select();

scButtons.addMembers([tsFews])




}


