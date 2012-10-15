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

            var map = new OpenLayers.Map(div.attr("id"));

            map.addLayers([new OpenLayers.Layer.OSM(
                "OpenStreetMap NL",
                "http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png",
                {buffer: 0})]);

            var extent = JSON.parse($(this).attr("data-bounds"));
            var bounds = new OpenLayers.Bounds(
                extent.minx, extent.miny,
                extent.maxx, extent.maxy);

            var imagelayer = new OpenLayers.Layer.Image(
                "Maximale waterdiepte",
                div.attr("data-image-url"),
                bounds,
                new OpenLayers.Size(0, 0),
                {isBaseLayer: false});

            map.addLayers([imagelayer]);
            map.addControl(new OpenLayers.Control.LayerSwitcher());
            map.zoomToExtent(bounds);

            // Add map to the list of known maps
            maps.push(map);

            // Register synchronizer
            map.events.register("moveend", map, synchronize_pan_zoom);
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