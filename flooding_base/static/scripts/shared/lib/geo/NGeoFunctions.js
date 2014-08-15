


function NIconStorage(defaults) {
    defaults = defaults || {};
    this.defaults.url = defaults.url || "images/" ;
    this.defaults.iconAnchor = defaults.iconAnchor  || new GPoint(16, 16);
    this.defaults.iconSize  = defaults.iconSize  || new GSize(32, 32);
    this.defaults.shadowAdd = defaults.shadowAdd    || "shadow.png"
    this.defaults.shadowSize = defaults.shadowSize  || new GSize(59, 32);

    this.icons = {};
}

NIconStorage.addIcon = function(id, icon) {

    if (this.icons[id]) {
        Log.logInfo("cannot add icon "+ id +" ,icon id already exist");
        return false;

    } else {
        this.icons[id] = id;
        return true;
    }
}

NIconStorage.getIcon= function(id) {
    if (this.icons[id]) {
        return this.icons[id];
    } else {
        Log.logInfo("requested icon "+ id +" is not in the iconStorage");
        return null;
    }
}

