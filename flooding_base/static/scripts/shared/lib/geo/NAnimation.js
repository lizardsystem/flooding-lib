function NAnimation(firstnr, lastnr, options ) {
    this.firstnr = firstnr;
    this.lastnr = lastnr;

    options = options || {};

    this.firstlabel = options.firstlabel || null;
    this.lastlabel = options.lastlabel || null;
    this.showDateLabel = options.showDateLabel || false;
    this.label_function = options.label_function || null;
    if (typeof(options.showValue) != 'undefined') {this.showValue = options.showValue;} else {this.showValue = true;}

    this.delta = options.delta || 3600;
    this.startnr = options.startnr || firstnr;
    this.autoplay = options.autoplay || false;
    this.autorewind = options.autorewind || false;
    this.autostopatend = options.autostopatend || false;

    this.display_firstnr = this.firstnr - this.startnr;
    this.display_lastnr =  this.lastnr - this.startnr;

}

NAnimation.prototype.updateSettings = function(firstnr, lastnr, options) {

    this.firstnr = firstnr || this.firstnr;
    this.lastnr = lastnr || this.lastnr;

    options = options || {};

    for (var obj in options) {
        this[obj] = options[obj];
    }

    this.display_firstnr = this.firstnr - this.startnr;
    this.display_lastnr =  this.lastnr - this.startnr;

};