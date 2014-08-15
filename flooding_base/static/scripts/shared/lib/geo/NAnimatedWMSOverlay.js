/****************************************************************/
/**** class:         NAnimatedWMSOverlay                         */
/**** description:     This class represents an overlay that...    */
/**** notes:        This class inherits from NWMSOverlay        */
/****************************************************************/


//options: legenda,
function NAnimatedWMSOverlay(id,name,options) {
    options = options || {};
    this.superclass(id,name, options);
    this.isInit = false;

    this.type = ANIMATEDWMSOVERLAY;

    this.animation = options.animation || null;
    this.setParams({timestep:0});
}

NAnimatedWMSOverlay.prototype = new NWMSOverlay();
NAnimatedWMSOverlay.prototype.superclass = NWMSOverlay;

