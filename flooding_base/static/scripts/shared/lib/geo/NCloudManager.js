console.log('NCloudManager laden ...');

/********************************************************************/
/**** class:         NCloudManager                                    */
/**** description:     This class manage and create Clouds for layers  */
/**** notes:       -                                                  */
/********************************************************************/


function NCloudManager(options) {
    options = options || {};

    this.max_percentage_width =  options.max_percentage_width || 0.7; //relative to map
    this.max_percentage_height = options.max_percentage_height || 0.7; //relative to map
    this.min_width = options.min_width || 250;
    this.max_width = options.max_width || 630; //groter dan 630 lijkt opmaak problemen op te leveren
    this.min_height = options.min_height || 250;
    this.max_height = options.max_height || 500;
    this.content_function = options.content_function || function() { return ""; };

    this.lastLocation = null;
    this.popup = null;
    this.layerIsInit = false;
    this.divname = 'popupSpan';

}

NCloudManager.prototype.destroy = function() {
    this.removePopup();
    if (this.popup !== null) {
        this.popup.destroy();
    }
};


NCloudManager.prototype.removePopup = function() {
    if (this.popup !== null) {
        map.removePopup(this.popup);
        this.popup.destroy();
        this.popup = null;
    }
};

NCloudManager.prototype.initLayer = function() {
    if (!this.layerIsInit) {
        this.layerIsInit = true;
    }
};

NCloudManager.prototype.openPopup = function(latlon) {
    this.initLayer();
    //first close previous
    this.removePopup();

    var this_ref = this;
    var closeBoxCallback = function() {
        this_ref.removePopup();
        //alert('close');
    };
    var closeBox = true;
    var size = this.getPopupSize(scMap.getWidth(), scMap.getHeight());
    size = new OpenLayers.Size(size.width, size.height);
    var popupContentHTML = '<div id="popupSpan" style="overflow:auto;height:100%">+ '+ST_LOADING_DATA+'</div>';

    if (this.popup === null) {
        this.popup = new OpenLayers.Popup.FramedCloud('hoi',
                                                      latlon,
                                                      size,
                                                      popupContentHTML,
                                                      null,
                                                      closeBox,
                                                      closeBoxCallback);

        this.popup.panMapIfOutOfView = true;
        //this.popup.minSize = size;
        this.popup.maxSize = size;
        this.popup.autoSize = false;
        //this.popup.data.overflow = (false) ? "auto" : "hidden";

        map.addPopup(this.popup);
        this.popup.show();
    } else {
        this.popup.toggle();
    }
};



NCloudManager.prototype.getPopupSize = function(width_map, height_map) {

    var width = Math.round(Math.max(Math.min(this.max_percentage_width * width_map, this.max_width),this.min_width));
    var height = Math.round(Math.max(Math.min(this.max_percentage_height * height_map, this.max_height),this.min_height));

    return {width:width, height:height };
};

/*
 *  refreshContent:
 *  - Called by navigation.js if date is changed
 *  - Called by NWMSOverlay.js if point is clicked
 *
 *  Input:
 *  - selectedLocation (id, lon, lat) of the selected location on the map
 *  - id: the id of the selectedLocation
 *  - name: the name of the selectedLocation
 *  - service_url: the url finaly used in the get_popup_content method (so a service.py)
 *  - params: extra params (used by NWMSOverlay to also send sobek_id and result_id)
 */
NCloudManager.prototype.refreshContent = function(selectedLocation, id, name, service_url, params) {

    if (this.popup === null || selectedLocation.id != this.lastLocation) {
        this.lastLocation = selectedLocation.id;
        this.openPopup( (new OpenLayers.LonLat(selectedLocation.lon, selectedLocation.lat)) );
    }

    var divname = this.divname;
    var size = this.getPopupSize(scMap.getWidth(), scMap.getHeight());
    var cloud_width = size.width-10;
    var cloud_height = size.height-15;

    this.updateHtmlSpan(divname, id, name, service_url, params, cloud_width, cloud_height);
};

NCloudManager.prototype.setHtmlSpan = function(html)
{
    try
    {
        document.getElementById(this.divname).innerHTML = html;

    } catch (e) {
        //fill graph tab
        if (document.getElementById(this.divname)) // may not be initialized yet
        {
            document.getElementById(this.divname).innerHTML = e ; //'No graph available';
        }
    }
};

NCloudManager.prototype.updateHtmlSpan = function(divname, id, name, service_url, params, cloud_width, cloud_height)
{
    try
    {
        html = this.content_function(id,name, service_url, params, cloud_width, cloud_height, this);
        document.getElementById(divname).innerHTML = html;

    } catch (e) {
        //fill graph tab
        if (document.getElementById(divname)) // may not be initialized yet
        {
            document.getElementById(divname).innerHTML = e ; //'No graph available';
        }
    }
};

NCloudManager.prototype.clear = function() {};
NCloudManager.prototype.selectLocation = function(id) {};

console.log('NCloudManager geladen ...');