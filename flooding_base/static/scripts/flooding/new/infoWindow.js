console.log('start laden flooding/new/infowindow ...');

function fnInfoWindowSettings() {

    iwMaps = new NLegendInfoWindow("Kaartlagen",{
        tabName: 'Kaartlagen' ,
	defaultSize : {width: 300, height:400 },
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

    iwLegend = new NLegendInfoWindow("Legenda",{
        tabName: 'Legenda' ,
	defaultSize : {width: 300, height:400 },
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

    return [iwLegend, iwMaps ];
}

console.log('klaar laden flooding/new/infowindow ...');

