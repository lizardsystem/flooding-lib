console.log('NLegendInfoWindow laden ...');

/************************************************************************************/
/**** class:         NLegendInfoWindow                                                */
/**** description:     The NLegendInfoWindow is a specific type of infowindow.            */
/****                This infowindow has its own class, since it has a lot of        */
/****                specific javascript layout properties (e.g. the sectionstack).  */
/************************************************************************************/

/*
 * @requires Isomorfic Smartclient
 */


/*** Constructor for creating a NLegendInfoWindow ***/
function NLegendInfoWindow(name, options) {
    console.log('constructing NLegendInfoWindow');
    options = options || {};
    this.superclass(name, options);

}

NLegendInfoWindow.prototype = new NInfoWindow();
NLegendInfoWindow.prototype.superclass = NInfoWindow;

/*** OVERRIDING the pre_init method from NInfoWindow ***/
NLegendInfoWindow.prototype.pre_init = function() {
    console.log('pre_init NLegendInfoWindow');

    this.pane = isc.Canvas.create({
        ID: "pane"+this.paneId,
        width: "100%",
        height: "100%",
        border: "none",
        overflow:"hidden",
        autoDraw: false
    });

    isc.SectionStack.create({
        ID: "legendManager",
        visibilityMode: "multiple",
        overflow:"auto",
        width: "100%", height: "100%"
    });

    this.legendStack = legendManager;
    this.pane.addChild(this.legendStack);
};

/*** Add the NLegendSection 'legend' to the section stack and select the defaultlegend ***/
NLegendInfoWindow.prototype.addLegendSection = function(legendSection){
    console.log("NLegendInfoWindow.prototype.addLegendSection ("+legendSection+")");
    console.log("legendSection id is "+legendSection.id);
    if (this.legendStack.getSectionNumber("section_" + legendSection.id)<0) {
        console.log('adding legend section with id=' + legendSection.id +
                    ' and title=' + legendSection.title);
        this.legendStack.addSection(
            {ID:"section_" + legendSection.id , title: legendSection.title, canCollapse: true, expanded: legendSection.initialExpanded, items: [legendSection.pane], overflow:'visible'}
        );
        legendSection.selectDefaultLegend();
    }
};

/*** Remove the NLegendSection 'legend' ***/
NLegendInfoWindow.prototype.removeLegendSection = function(legendSection) {
    console.log('removing legend section with id=' + legendSection.id +
                ' and title=' + legendSection.title);
    this.legendStack.removeSection("section_" + legendSection.id);
};

/*** Override reloadIfNeeded function ***/
NLegendInfoWindow.prototype.reloadIfNeeded = function() {};


