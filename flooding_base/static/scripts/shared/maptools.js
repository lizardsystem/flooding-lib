/*      Function
 *      Zoom to boundbox
 *input:    (1) Gmap object
 *      (2)     Optie1  Item with south, north, west, east and (optional) projection
 *          optie2  GLatLngBounds or NBounds object
 *Dependencies: openLzyers
 *
 *
 */

function Ozoom(map_ ,bounds ) {
    if (bounds) {
        if (bounds.getCenterLonLat) { //dan moet dit een openlayer.Bounds of OBounds object zijn
            var obounds = bounds;
        } else {
            var obounds = new OBounds(bounds);
        }
        if (obounds.validRect()) {
            //map_.getZoomForExtent(trans);

            map_.zoomToExtent(obounds);
        }
    }
}


/*      Function
 *      Resize the map
 *input:    (1) Name of Map
 *      (2) heights of other elements in the page
 *      (3 optional) widths of other elements in page. If not given or null, the width is not adjusted
 *      (4 optional) options: minHeight or minWidth of map, default: 300px
 *Dependencies: None
 *
 *remarks:  needed for Internet Explorer. The 'width' is needed in IE 6.0.
 *example:  set the resize function to the load and onresize events of the body
 *      <body onload = "NresizeMap('map', 90 ,220);load();" onunload="GUnload();" onresize="NresizeMap('map', 90,220 )" >
 *
 */

function NresizeMap(mapName, otherHeights, otherWidths, options ) {
    options = options || {};

    var minHeight =  options.minHeight || 300;

    var mapdiv = document.getElementById(mapName);


    if ((document.body.clientHeight - otherHeights) < minHeight) {
        var height = minHeight;
    } else {
        var height = document.body.clientHeight - otherHeights;
    }

    mapdiv.style.height = (height) + "px";

    if (otherWidths) { //optional if otherWidhts are given

        var minWidth =  options.minWidth || 300;

        if ((document.body.clientWidth - otherWidths) < minWidth) {
            var width = minWidth;
        } else {
            var width = document.body.clientWidth - otherWidths;
        }

        mapdiv.style.width = (width) + "px";
    }
}

/*      Class
 *      GLatLngBounds() met een andere invoer en het ondersteunen van RDS coordinaten
 *input:    (1) map object
 *      (2 not supported yet) pgw; a link to a pgw and image file, from where the bounds can be dtermined (north, south, west and east of input 1 are not needed in this case
 *Dependencies: Gmap
 *
 *functions:    same as GLatLngBounds()
 *
 */

//always translate to google mercator 900913
function OBounds(inputs, mapExtent) {

    //for testing, take properties to 'this.'. can be removed after testing

    this._north = inputs.north;
    this._south = inputs.south;
    this._west = inputs.west;
    this._east = inputs.east;

    this._projection = new String(inputs.projection)|| "wgs84";

    if (this._projection.toLowerCase()=='rds'||this._projection == '28992'||this._projection == 28992) { // 28992
        //Rijksdriehoekstelsel
        if (mapExtent) {
            var mapExtent = mapExtent.transform( new OpenLayers.Projection("EPSG:900913") , new OpenLayers.Projection("EPSG:4326") )
            var extent = mapExtent.toArray();
            calc_extent_south = Math.max(wgs2rds(extent[1],(extent[0]+extent[2])/2).y ,this._south);
            calc_extent_north = Math.min(wgs2rds(extent[3],(extent[0]+extent[2])/2).y ,this._north);
            calc_extent_east = Math.min(wgs2rds( (extent[1]+extent[3])/2,extent[2]).x, this._east);
            calc_extent_west = Math.max(wgs2rds( (extent[1]+extent[3])/2,extent[0]).x,this._west );
        } else {
            calc_extent_south = this._south;
            calc_extent_north = this._north
            calc_extent_east = this._east;
            calc_extent_west = this._west;
        }

        this.extend( ORDLonLat(this._west, ((calc_extent_south+calc_extent_north)/2) ));
        this.extend( ORDLonLat( this._east,((calc_extent_south+calc_extent_north)/2)));
        this.extend( ORDLonLat( ((calc_extent_east+calc_extent_west)/2), this._north));
        this.extend( ORDLonLat( ((calc_extent_east+calc_extent_west)/2), this._south));
        
        this.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913") );

    } else if (this._projection.toLowerCase()=='epsg:900913'|| this._projection.toLowerCase()==900913){ //google mercator 900913
        this.extend(new OpenLayers.LonLat(this._west, this._north));
        this.extend(new OpenLayers.LonLat(this._east, this._south));
 
     }  else { //wgs84
        this.extend(new OpenLayers.LonLat(this._west, this._north));
        this.extend(new OpenLayers.LonLat(this._east, this._south));

        this.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913") );
    }
}

OBounds.prototype = new OpenLayers.Bounds();
//NBounds.prototype.constructor = NBounds;
OBounds.prototype.superclass = OpenLayers.Bounds;

OpenLayers.Bounds.prototype.validRect = function() {
   if ((this.getWidth() >0 ) &&(this.getHeight() >0 ) ) {
    return true;
   }else{
    return false;
   }
}



