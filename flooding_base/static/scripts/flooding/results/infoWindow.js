// Uses CONFIG from flooding_config.js

console.log('start laden flooding/result/infowindow ...');

function frInfoWindowSettings() {
    console.log('entering method: "frInfoWindowSettings"');
    iwScenarioInformation = new NInfoWindow("Scenario Informatie",{

        tabName: ST_INFO ,
	defaultSize : {width: 420, height:400 },
	canClose: false,
	canMax: false,
	canMin: false,
	showTitle: true,
	preLoad:false,
	enabled:false,

	isForm:false,
	baseUrl: flooding_config.root_url + "flooding/infowindow/",
	params:{scenarioid:1,action:'information'},
	type: HTMLPANE,


        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });

    iwScenarioRemarks = new NInfoWindow("Scenario Opmerkingen",{

        tabName: ST_REMARK,
	defaultSize : {width: 420, height:320 },
	canClose: false,
	canMax: false,
	canMin: false,
	showTitle: true,
	preLoad:false,
	enabled:false,

	isForm:true,
	baseUrl: flooding_config.root_url + "flooding/infowindow/",
	params:{scenarioid:1,action:'remarks'},
	type: HTMLPANE,


        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });

    iwApprovalInformation = new NInfoWindow("Keuringen",{
        tabName: ST_APPROVAL,
	defaultSize : {width: 420, height:400 },
	canClose: false,
	canMax: false,
	canMin: false,
	showTitle: true,
	preLoad:false,
	enabled:false,

	isForm:true,
	baseUrl: flooding_config.root_url + "flooding/infowindow/",
	params:{scenarioid:1,action:'approval'},
	type: HTMLPANE,

        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });

    iwEdit = new NInfoWindow("Scenario bewerken",{
        tabName: ST_EDIT,
	defaultSize : {width: 420, height:400 },
	canClose: false,
	canMax: false,
	canMin: false,
	showTitle: true,
	preLoad:false,
	enabled:false,

	isForm:false,
	baseUrl: flooding_config.root_url + "flooding/infowindow/",
	params:{scenarioid:1,action:'edit'},
	type: HTMLPANE,

        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });

    iwLegend = new NLegendInfoWindow("Legenda",{
        tabName: ST_LEGEND ,
	defaultSize : {width: 420, height:400 },
	canClose: false,
	canMax: false,
	canMin: false,
	showTitle: true,
	preLoad:false,
	enabled:false,
	rootURL: flooding_config.root_url,
	isForm:false,

        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });

    iwArchive = new NInfoWindow("Archief",{
        tabName: ST_ARCHIVE,
    	defaultSize : {width: 420, height:400 },
    	canClose: false,
    	canMax: false,
    	canMin: false,
    	showTitle: true,
    	preLoad:false,
    	enabled:false,
    	baseUrl: flooding_config.root_url + "flooding/infowindow/",
    	params:{scenarioid: 1, action: 'archive'},
    	type: HTMLPANE,
    	isForm:true,

        onInit: function(isSelected){

        },
        onRefreshContent:function(isSelected,reason){

        },
        onSelect: function() {

        },
        onUnSelect: function() {

        },
        onDestroy: function() {

        }
    });


    return [iwScenarioInformation, iwLegend, iwScenarioRemarks, iwApprovalInformation, iwEdit, iwArchive ];
}

console.log('klaar laden flooding/result/infowindow ...');
