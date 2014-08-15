console.log('NLegend laden ...');

/****************************************************************************/
/**** class:         NLegend                                                    */
/**** description:     The section that contains Legend information            */
/****************************************************************************/

/*
 * @requires Isomorfic Smartclient
 *
 */

/**** Identity number generator - using the global variable Nget_id_nr ****/
var Nget_id_nr = 0;
function Nget_id() {
    return Nget_id_nr++;
}

function NLegendSection(id, options) {
    this.id = 'legendSection_' + Nget_id();//id;
    this.name = options.name;
    console.log('NLegendSection aangemaakt met id=' + this.id + ' en name=' + this.name);

    this.title = options.title;
    this.initialExpanded = options.initialExpanded || false;
    this.legends = options.legends;
    this.rootURL = options.rootURL || "";
    this.baseURL = options.baseURL;
    this.defaultLegend = options.defaultLegend;
    this.overlay = options.overlay;
    var this_ref =this;
    this.dropdownButton = isc.DynamicForm.create({
        width:"*", minWidth:300,
        numCols:1,
        fields: [
            {
                name: "selectLegendButton_"+this.id, showTitle: false, width:"*",
                type: "select",
                change: function(form,item,value) {
                    this_ref.selectLegend({id:value, name:item.valueMap[value]});
                }
            }
        ]
    });

    this.legendPane =  isc.HTMLPane.create({
        width:"100%",
        overflow:"visible",
        border: "none",
        autoDraw: true
    });

    this.pane = isc.VLayout.create({
        width:"100%",
        overflow:"visible",
        members: [this.dropdownButton, this.legendPane],
        autoDraw: false
    });
}

/*** Set the available legends for this section, such that they are also
     visible in the dropdown button. ***/
NLegendSection.prototype.setLegends = function(legends){
    console.log('LegendSection.setLegends with legends='+legends);
    this.legends = legends;

    var valuemap = {};
    for(var i=0; i<legends.length; i++){
        valuemap[legends[i].id]=legends[i].name;
    }

    this.dropdownButton.setValueMap("selectLegendButton_" + this.id, valuemap);
    if (legends.length == 1) {
        this.dropdownButton.hide();
    }
};

/*** Sets a default legend for this legendSection ***/
NLegendSection.prototype.setDefaultLegend = function(legend){
    console.log('LegendSection.setDefaultLegend with legend='+legend);
    this.defaultLegend = legend;
};

/*** Selects a legend:
     - it changes the pane for showing the right legend,
     - it changes the dropdownbutton to the right value,
     - it tells the overlay to retrieve a new layer from the server. ***/
NLegendSection.prototype.selectLegend = function(legend){
    console.log("In selectLegend");
    if(typeof legend !== 'undefined')
    {
        console.log('Selecting legend with id=' + legend.id);
        console.log('Setting pane contentsURL='+ this.rootURL + this.baseURL + legend.id);
        console.log("this.legendPane = "+this.legendPane);
        dynamic_legend.set_legend_contents(
            this.legendPane, this.rootURL + this.baseURL + legend.id);
        this.dropdownButton.setValue("selectLegendButton_" + this.id, legend.id);
        this.overlay.setActiveLegend(legend);

    } else {
        console.log("legend is undefined");
    }
};

/*** Shortcut function for selecting the default legend ***/
NLegendSection.prototype.selectDefaultLegend = function(){
    console.log('selecting default legend (= '+this.defaultLegend + ")");
    this.selectLegend(this.defaultLegend);
};
