console.log('NOverlay laden ...');

/****************************************************************************/
/**** class:         NOverlay                                                */
/**** description:     The base class for an overlays                            */
/****************************************************************************/

/*
  NOverlay constructor sets the following properties on the object, using the arguments:
  id, name: from the first two arguments, others are all from options

  layerIndex (default 0)
  geoType
  valueType
  rootURL (default "")
  app
  visible
  displayInLayerSwitcher (default false)
  legendWindow

  legendBaseURL (default an URL constructed using options.settingsRequestParams.result_id)
  legendSection (using the other options)

  Also, this.activeLegend is set to null.
*/

/*
  Defines the following methods:

  NOverlay.prototype.hideLegendSection
  NOverlay.prototype.setAvailableLegends
  NOverlay.prototype.setDefaultLegend
  NOverlay.prototype.showLegendSection
*/

/*
 * @requires Isomorfic Smartclient
 *
 */

function NOverlay(id,name,options) {
    options = options || {};

    this.id = id;
    this.name = name;
    this.layerIndex = options.layerIndex || 0;

    this.geoType = options.geoType; //geotype
    this.valueType = options.valueType; //valuetype
    this.rootURL= options.rootURL || "";
    this.activeLegend = null;
    this.app = options.app;
    this.visible = options.visible;

    this.displayInLayerSwitcher = options.displayInLayerSwitcher || false;

    this.legendWindow = options.legendWindow;
    var legend_url;
    try {
        legend_url = 'visualization/legend/?presentationlayer_id=' + options.settingsRequestParams.result_id + '&object_id=';
    }
    catch (error){
        legend_url = 'visualization/legend/?object_id=';
    }


    this.legendBaseURL = options.legendBaseURL || legend_url;
    console.log("Creating LegendSection with baseURL "+this.legendBaseURL);

    this.legendSection = new NLegendSection('legendsection_' + this.id,
                                            {title:ST_LEGEND_OF + ' ' + name,
                                             initialExpanded: true,
                                             baseURL: this.legendBaseURL,
                                             rootURL: this.rootURL,
                                             overlay: this });
}


/*** Sets the default legend, by calling the right method on the legendSection ***/
NOverlay.prototype.setDefaultLegend = function(legend) {
    this.legendSection.setDefaultLegend(legend);
};


/*** Sets the available legends, by calling the right method on the legendSection ***/
NOverlay.prototype.setAvailableLegends = function(legends) {
    console.log('Set available legends');
    this.legendSection.setLegends(legends);
};


/*** Shows the the legendsection related to this overlay, by calling the right method on the legendSection ***/
NOverlay.prototype.showLegendSection = function () {
    console.log('Show legend section (= ' + this.legendSection + ")");
    this.legendWindow.addLegendSection(this.legendSection);
};


/*** Hides the the legendsection related to this overlay, by calling the right method on the legendSection ***/
NOverlay.prototype.hideLegendSection = function(){
    console.log('Hide legend section');
    this.legendWindow.removeLegendSection(this.legendSection);
};