/* The variables below hold the current setting for the legend and max value
   of the legend. They are used by map layers with dynamic legends (Pyramids, and
   new animations) and should be set by the user in the future. */

var dynamic_legend = (function () {
    var current_legend_pane = undefined;
    var contents_url = undefined;

    return {
        // Undefined means: use max value of the data
        maxvalue: undefined,

        // Values should be matplotlib colormap names, eg. 'PuBu'.
        // Undefined means: use this resulttype's default colormap.
        colormap: undefined,

        set_legend_contents: function(legend_pane, url) {
            console.log("Set legend contents to " + url);
            current_legend_pane = legend_pane;
            contents_url = url;

            this.set_contents_url();
        },

        set_contents_url: function () {
            var url = contents_url;

            console.log("url = " + url);
            console.log("current_legend_pane = " + current_legend_pane);

            if (!url || !current_legend_pane) {
                return;
            }

            if (typeof this.maxvalue !== 'undefined') {
                url += '&maxvalue=' + this.maxvalue;
            }
            if (typeof this.colormap !== 'undefined') {
                url += '&colormap=' + this.colormap;
            }

            // Actually set the contents URL.
            current_legend_pane.setContentsURL(url);

            // Also update layer
            if (appManager.selectedApp.overlayManager.activeOverlay) {
                appManager.selectedApp.overlayManager.activeOverlay.redraw();
            }
        },

        set_maxvalue: function(maxvalue) {
            if (maxvalue !== this.maxvalue) {
                this.maxvalue = maxvalue;
                this.set_contents_url();
            }
        },

        set_colormap: function(colormap) {
            if (colormap !== this.colormap) {
                this.colormap = colormap;
                this.set_contents_url();
            }
        },

        reset: function () {
            this.colormap = undefined;
            this.maxvalue = undefined;
        }
    };
}());


