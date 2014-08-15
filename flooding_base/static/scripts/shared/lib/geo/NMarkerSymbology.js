
COLORLEGENDA = 1;
MARKERLEGENDA = 2;
ZOOMLEGENDA = 3;

RANGEEQUAL = 1;

//options: unit,rangeType
//type
function NMarkerSymbology(name, type, options){
    options = options ||
    {};

    this.name = name;
    this.unit = options.unit || "";
    this.type = options.type || COLORLEGENDA; //
    this.rangeType = options.rangeType || "rangeUpper";
    this.defaultMarker = options.defaultMarker || "";
    this.defaultSelectedMarker = options.defaultSelectedMarker || "";

    if (options.valueMap) {
        this.data = options.valueMap;
        this.loaded = true;

        if (this.rangeType == RANGEEQUAL) {
            this.dataMap = {};
            for (var i = 0; i < this.data.length; i++) {
                this.dataMap[this.data[i][0]] = {};
                this.dataMap[this.data[i][0]].nr = i;
                this.dataMap[this.data[i][0]].unselected = this.data[i][1];
                if (this.data[i][2]) {
                    this.dataMap[this.data[i][0]].selected = this.data[i][2];
                }
                else {
                    this.dataMap[this.data[i][0]].selected = this.data[i][1];
                }
            }
        }
    }
    else {
        this.data = new Array();
        this.loaded = false;
    }
}

NMarkerSymbology.prototype.clearValueMap = function() {
    this.valueMap = null;
    this.loaded = false;
}

NMarkerSymbology.prototype.setValueMap = function(valueMap) {
    this.data = valueMap;
    this.loaded = true;
}

NMarkerSymbology.prototype.fetchData = function(url, callback) {
    this.fetchValueMap(url,callback);
}

NMarkerSymbology.prototype.fetchValueMap = function(url, callback) {

    if (this.loaded == false) {
        var ref = this;

        pgwFile.fetchData({
            file: url
            }, function(request, rdata, response){
                if (rdata[0].status == true) {
                    var lines = rdata[0].data.split(";"); //Gdownload : /n
                    //TO DO: laat data
                    for (var i = 0 ; i < lines.getLength() ; i++ ) {
                        var field = lines[i].split(",");
                        ref.data[i] = {};
                        ref.data[i].color = field[1];
                        ref.data[i].value = field[0];
                    }
                    ref.loaded = true;
                    callback(ref, ref.data, "");
                } else {
                    console.log("fetching legenda file mislukt");
                }
        });
    } else {
        this.loaded = true;
        callback(this, this.data, "");
    }

}

NMarkerSymbology.prototype.getHTML = function() {
    var html = "";
    html += '<div id="legenda"> <table>\n';

    for (var i=1; i < this.data.getLength()-1; i++) {
        html += '<tr><td><div class = "classLegenda" style ="background-color: ' + this.data[i].color + ';"></div></td><td> \>'+ this.data[i].value + '</td></tr>\n';
    }
    html += '</table></div>\n';
    return html;
}


NMarkerSymbology.prototype.getColor = function(value) {

    if (this.boundaries[0] > this.boundaries[1]){
        var factor = -1;
    }
    else {

        var factor = 1;
    }

    for (var i = 0; i < this.boundaries.length; i++) {
        if ((factor*value) < (factor*this.boundaries[i])) {
            if (this.colors.length >= i) {
                return (this.colors[i]);
            } else {
                return (this.colors[this.colors.length-1]);
            }
        }
        return this.colors[this.boundaries.length];
    }
}

NMarkerSymbology.prototype.getZoom = function(value) {

	if (this.dataMap[value]) {
    	return this.dataMap[value].nr;
    } else {
    	return -1;
    }
}

NMarkerSymbology.prototype.getIcon = function(value,selected) {

    if (this.rangeType == RANGEEQUAL) {
        if (this.dataMap[value]) {
            if (selected) {
                return this.dataMap[value].selected;
            } else {
                return this.dataMap[value].unselected;
            }
        } else {
            if (selected) {
                return this.defaultSelectedMarker;
            } else {
                return this.defaultMarker;
            }
        }

    } else {
        if (this.boundaries[0] > this.boundaries[1]){
            var factor = -1;
        } else {
            var factor = 1;
        }

        for (var i = 0; i < this.boundaries.length; i++) {
            if ((factor*value) < (factor*this.boundaries[i])) {
                if (this.icons.length >= i) {
                    return (this.icons[i]);
                } else {
                    return (this.icons[this.icons.length-1]);
                }
            }
            return this.icons[this.boundaries.length];
        }
    }
}

