
function fnOverlaySettings() {

    fnbreachLayer = new NMarkerOverlay("breach_new","Doorbraaklocatie nieuw",map,null,{
        //legendWindow: iwLegend,
        canSelect: true,
        canUnselect: false,
        multipleSelect:false,
        displayInLayerSwitcher:true,
        defaultMarker:icons["rondje"],
        defaultSelectedMarker:icons["circleyellow"],
        layerIndex:60,
        isDataTreeFormat:false,
        labelIsPoint:"isbreach",
        idfield:"id",
        latfield:"y",
        lonfield:"x",
        app: 'flooding',
	visibile: true,
        clickMarker: function(isSelect,marker,loc){
            var node = fnBlockBreaches.tree.data.findById(marker.Nid);
            fnBlockBreaches.tree.deselectAllRecords();
            fnBlockBreaches.tree.selectRecord(node);
            fnBlockBreaches.tree.openFolder(fnBlockBreaches.tree.data.findById(node.parentid));
	    fnBlockBreaches.tree.redraw();
            //scroll to position in treegrid
            var height = fnBlockBreaches.tree.getRecordIndex(node)* fnBlockBreaches.tree.cellHeight - 0.15* fnBlockBreaches.tree.getHeight();
            fnBlockBreaches.tree.body.scrollTo(0,height);

            fnBlockBreaches.tree.leafClick(null,node,null);
        },
        onMouseOver: function(marker, event) {
            if (lastmarker != marker) {
	        console.log(marker.loc.name);
		if (typeof(label) == 'undefined') {
		    initLabel();
		}
		label.moveTo(event.clientX+5,event.clientY-25);
		label.show();
		label.setContents(marker.loc.name);
	    }
	    lastmarker = marker;

	},
	onMouseOut: function(marker,event) {
	    label.hide();
	    lastmarker = null;

	}
    });

    var CUTOFFLOCATION_TYPE_LOCK = 1
    var CUTOFFLOCATION_TYPE_CULVERT = 2
    var CUTOFFLOCATION_TYPE_WEIR = 3
    var CUTOFFLOCATION_TYPE_BRIDGE = 4
    var CUTOFFLOCATION_TYPE_UNDEFINED = 5


    var loccutoffsZoomLegend = new NMarkerSymbology('afsluitlocaties',ZOOMLEGENDA,{
        rangeType: RANGEEQUAL,
        valueMap: [
            [[CUTOFFLOCATION_TYPE_UNDEFINED],0.001,25000]
        ]
    });

    var loccutoffsLegendNew = new NMarkerSymbology('afsluitlocaties',MARKERLEGENDA,{
	rangeType: RANGEEQUAL,
	defaultMarker:icons["squaregreen"],
	defaultSelectedMarker:icons["squarered"],
	valueMap: [
	    [[CUTOFFLOCATION_TYPE_LOCK],icons['sluisgreen'],icons['sluisred']],
	    [[CUTOFFLOCATION_TYPE_CULVERT],icons['culvertgreen'],icons['culvertred']],
	    [[CUTOFFLOCATION_TYPE_BRIDGE],icons['bridgegreen'],icons['bridgered']],
	    [[CUTOFFLOCATION_TYPE_WEIR],icons['sluisgreen'],icons['sluisred']]
	]
    });


    fnLoccutoffsLayer = new NMarkerOverlay("resultLoccutoffs","Afsluit locaties",map,null,{
        legendField: 'type',
        canSelect: true,
        canUnselect: true,
        multipleSelect:true,
        displayInLayerSwitcher:true,
	defaultMarker:icons["circlegreen"],
	defaultSelectedMarker:icons["circlered"],
	legend: loccutoffsLegendNew,
	legendField: 'type',
	layerIndex:55,
	zoomLegend: loccutoffsZoomLegend,
	zoomLegendField:'type',
	isDataTreeFormat:false,
	idfield:"id",
        latfield:"y",
        lonfield:"x",
        app: 'flooding',
	visibile: true,
	clickMarker: function(isSelect,marker,loc){
	    if (isSelect) {
		if (loc.tdef == ""){
		    loc.tdef = "0:00";
		}

		var type_icon = loccutoffsLegendNew.getIcon(loc.type, true);
		var record = {id:loc.id,type:type_icon.url,name:loc.name, action:1, tclose: loc.tdef};
		listLoccutoffs.data.addAt(record);
	    } else {
		listLoccutoffs.data.remove(listLoccutoffs.data.find("id",loc.id));
	    }
	}
    });


    existing_embankments_layer = new NWMSOverlay("Extra embankement", "Aangepaste keringen", {
	rootURL: flooding_config.root_url,
	singleTile:true,
	geoType:3,
	displayInLayerSwitcher:true,
	valueType:1,
	layerIndex:45,
	getFramesFromRequest:true,
	frameUrl: locationFloodingData,
	framesRequestParams: {
	    action:'get_existing_embankments_shape',
	    only_selected:True
	},
	app: 'flooding',
	visibile: false
    });

    return {overlays: [fnbreachLayer,fnLoccutoffsLayer,existing_embankments_layer]};
}
