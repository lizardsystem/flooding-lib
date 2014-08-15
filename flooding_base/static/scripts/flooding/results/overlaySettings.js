
lastmarker = null;

function initLabel() {
    if (typeof(label) == 'undefined') {
	isc.Label.create({
  	    ID: "label",
	    showFocusedAsOver:false,
	    wrap:false,
	    left:10,
	    height:24,
	    autoFit:true,
	    styleName:"textItem",
	    overflow:"hidden",
	    autoDraw:false,
	    top:5,
	    showShadow: true, shadowSoftness: 2, shadowOffset: 3,
	    dynamicContents:true,
	    showTitle:false,
	    showFocused:false
	});
    }
}


function frOverlaySettings() {


    frbreachLayer = new NMarkerOverlay("breach","Doorbraaklocatie",map,null,{
        //legendWindow: iwLegend,
        canSelect: true,
        canUnselect: false,
        multipleSelect:false,
        displayInLayerSwitcher:true,
        layerIndex:60,
        defaultMarker:icons["rondje"],
        defaultSelectedMarker:icons["circleyellow"],
        isDataTreeFormat:false,
        labelIsPoint:"isbreach",
        idfield:"id",
        latfield:"y",
        lonfield:"x",
        clickMarker: function(isSelect,marker,loc){
            var node = frBlockBreaches.tree.data.findById(marker.Nid);
            frBlockBreaches.tree.deselectAllRecords();
            frBlockBreaches.tree.selectRecord(node);
            frBlockBreaches.tree.openFolder(frBlockBreaches.tree.data.findById(node.parentid));
            frBlockBreaches.tree.redraw();
            //scroll to position in treegrid
            var height = frBlockBreaches.tree.getRecordIndex(node)* frBlockBreaches.tree.cellHeight - 0.15* frBlockBreaches.tree.getHeight();
            frBlockBreaches.tree.body.scrollTo(0,height);

            frBlockBreaches.tree.leafClick(null,node,null);

        },
        onMouseOver: function(marker, event) {
            if (lastmarker != marker) {
	        console.log(marker.loc.name);
		if (typeof(label) == 'undefined') {
		    initLabel();
		}
		label.moveTo(event.clientX+5,event.clientY-25);
		label.setContents(marker.loc.name);
		label.show();
	    }
	    lastmarker = marker;

	},
	onMouseOut: function(marker,event) {
	    label.hide();
	    lastmarker = null;

	},
	app: 'flooding',
	visibile: true
    });

    var CUTOFFLOCATION_TYPE_LOCK = 1
    var CUTOFFLOCATION_TYPE_CULVERT = 2
    var CUTOFFLOCATION_TYPE_WEIR = 3
    var CUTOFFLOCATION_TYPE_BRIDGE = 4
    var CUTOFFLOCATION_TYPE_UNDEFINED = 5


    var loccutoffsZoomLegend = new NMarkerSymbology('afsluitlocaties',ZOOMLEGENDA,{
        rangeType: RANGEEQUAL,
        valueMap: [
            [[CUTOFFLOCATION_TYPE_LOCK,CUTOFFLOCATION_TYPE_WEIR,CUTOFFLOCATION_TYPE_CULVERT],0.001,25000],
            [[CUTOFFLOCATION_TYPE_BRIDGE],0.001,25000]
        ]
    });

    var loccutoffsLegendResult = new NMarkerSymbology('afsluitlocaties',MARKERLEGENDA,{
        rangeType: RANGEEQUAL,
        defaultMarker:icons["squarered"],
        defaultSelectedMarker:icons["squarered"],
        valueMap: [
            [[CUTOFFLOCATION_TYPE_LOCK],icons['sluisred']],
            [[CUTOFFLOCATION_TYPE_CULVERT],icons['culvertred']],
            [[CUTOFFLOCATION_TYPE_BRIDGE],icons['bridgered']],
            [[CUTOFFLOCATION_TYPE_WEIR],icons['sluisred']]
        ]
    });

    frLoccutoffsLayer = new NMarkerOverlay("resultLoccutoffs","Afsluit locaties",map,null,{
        //legendWindow: iwLegend,
        legend: loccutoffsLegendResult,
        legendField: 'type',
        canSelect: false,
        canUnselect: false,
        multipleSelect:false,
        layerIndex:55,
        displayInLayerSwitcher:true,
        defaultMarker:icons["circlered"],
        isDataTreeFormat:false,
        idfield:"id",
        latfield:"y",
        lonfield:"x",
        clickMarker: function(isSelect,marker,loc){

        },
        onMouseOver: function(marker, event) {
            if (lastmarker != marker) {
	        console.log(marker.loc.name);
		if (typeof(label) == 'undefined') {
		    initLabel();
		}
		label.moveTo(event.clientX+5,event.clientY-25);
		label.show();
		label.setContents(marker.loc.name + ', dicht na: ' +  intervalFormatter( new Date(marker.loc.tclose * 1000 ) ));
	    }
	    lastmarker = marker;
	},
	onMouseOut: function(marker,event) {
	    label.hide();
	    lastmarker = null;
	},
	app: 'flooding',
	visibile: true

    });

    frExtraEmbankmentLayer = new NWMSOverlay("Extra embankement", "Aangepaste keringen", {
	rootURL: flooding_config.root_url,
	singleTile:true,
	geoType:3,
	valueType:1,
	layerIndex:40,
	getFramesFromRequest:true,
	frameUrl: locationFloodingData,
	framesRequestParams: {
	    action:'get_existing_embankments_shape',
	    only_selected:True
	},
	app: 'flooding',
	visibile: false
    });


    //frExtraRegionGrids.legendSection.setLegends([{"id": 10, "name": "hoogte grid"}]);
    //frExtraRegionGrids.showLegendSection();

    return  {overlays:[frbreachLayer,frLoccutoffsLayer, frExtraEmbankmentLayer]};
}
