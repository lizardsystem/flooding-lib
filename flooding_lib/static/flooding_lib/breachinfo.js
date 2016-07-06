/*global $, OpenLayers */
(function () {
    "use strict";

    $(function () {
        // Fill all divs with 'class "map"' with an openlayers map, use their
        // 'data-bounds' as an extent and their 'data-image-url' as an image
        // to show.

        var maps = []; // For updating when panning etc

        var synchronize_pan_zoom = function () {
            // Synchronize panning and zooming
            // Use 'map.updating' to prevent one map from recursively
            // updating the other while the other is updating the
            // first while etc...
            if (!this.updating) {
                this.updating = true;

                var center = this.getCenter();
                var zoom = this.getZoom();

                for (var i=0; i < maps.length; i++) {
                    var synchronize_map = maps[i];
                    if (!synchronize_map.updating) {
                        synchronize_map.updating = true;
                        synchronize_map.panTo(center);
                        synchronize_map.zoomTo(zoom);
                        synchronize_map.updating = false;
                    }
                }

                this.updating = false;
            }
        };

        $(".map").each(function () {
            var div = $(this);

            var data_bounds = div.attr("data-bounds");
            if (data_bounds !== "") {
                var extent = JSON.parse(data_bounds);
                var bounds = new OpenLayers.Bounds(
                    extent.minx, extent.miny,
                    extent.maxx, extent.maxy);

                var map = new OpenLayers.Map(div.attr("id"), {
                    maxExtent: bounds,
                    projection: new OpenLayers.Projection("EPSG:3857")
                });

                map.addLayer(
                    new OpenLayers.Layer.OSM(
                        "OpenStreetMap NL",
                        "http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png",
                        {buffer: 0}));

                var url = div.attr("data-url");
                var layers = div.attr("data-pyramid");

                var params = {
                    layers: layers,
                    styles: "PuBu:0:2",
                };

                map.addLayer(new OpenLayers.Layer.WMS(
                    "pyramid", url, params, {
                        singleTile: true,
                        isBaseLayer: false,
                        displayInLayerSwitcher: true,
                        units: 'm'
                    }));

                map.zoomToExtent(bounds);
                maps.push(map);
                // Register synchronizer
                map.events.register("moveend", map, synchronize_pan_zoom);
            }
        });
    });

    // Checkboxes that toggle display of maps
    $(function () {
        var set_checkbox_and_toggle_display = function(checkbox, status) {
            checkbox.attr("checked", status);
            var scenarioid = checkbox.attr("data-scenario-id");
            var mapdiv = $("#mapcontainer-"+scenarioid);
            if (status) {
                mapdiv.show();
            } else {
                mapdiv.hide();
            }
        };

        $("#checkbox-all").change(function() {
            // The all checkbox changed -- set all the individual scenario
            // checkboxes too, and show/hide divs accordingly
            var checkbox = $(this);
            var ischecked = checkbox.is(":checked");

            $(".checkbox-scenario").each(function () {
                set_checkbox_and_toggle_display($(this), ischecked);
            });
        });

        $(".checkbox-scenario").click(function() {
            // An individual checkbox was clicked -- toggle display value
            set_checkbox_and_toggle_display($(this), $(this).is(":checked"));
        });
    });
})();
