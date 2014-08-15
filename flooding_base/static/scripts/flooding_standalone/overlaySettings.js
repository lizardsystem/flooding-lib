
function stOverlaySettings() {



    stbreachLayer = new NMarkerOverlay("breach","Doorbraaklocatie",map,null,{
        canSelect: true,
        canUnselect: false,
        multipleSelect:false,
        defaultMarker:icons["circlegreen"],
        defaultSelectedMarker:icons["circlered"],
        isDataTreeFormat:false,
        //labelIsPoint:"isbreach",
        idfield:"id",
        latfield:"y",
        lonfield:"x",
        displayInLayerSwitcher:false,
        clickMarker: function(isSelect,marker,loc){
            var node = stBlockBreaches.tree.data.findById(marker.Nid);
            stBlockBreaches.tree.deselectAllRecords();
            stBlockBreaches.tree.selectRecord(node);
            stBlockBreaches.tree.leafClick(null,node,null);
            //TO DO?: scroll naar selected node
            //alert(this.icon.url); OpenLayers.Event.stop(evt);
        }
    });

  
	stbreachLayer.addToMap();
    return  {overlays:[stbreachLayer]};
}










