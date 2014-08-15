console.log('loading NToolbarManager ...');

/****************************************************************************/
/**** class: 		NToolbarManager    		            	                */
/**** description: 	The NToolbarManager 'manages' the NToolbar's.           */
/****************************************************************************/

function NToolbarManager(toolstripId) {
    this.toolstripId = toolstripId;
    this.toolstrip = [];
    
    this.pre_init(); 
}

/**** Pre-initializing the NToolbarManager - setting some defaults ****/
NToolbarManager.prototype.pre_init = function() {
	isc.ToolStrip.create({
	    ID:"scToolstrip",
	    //width: 140,
	    height:25,
	    membersMargin:10,
	    members: [  ],
	    styleName:'toolStrip2',
	    autoDraw:false
	});
	this.screenToolstrip = scToolstrip;
	scButtons.addMembers([this.screenToolstrip])
	
	this.seperator = isc.ToolStripSeparator.create({hSrc:'[SKIN]separator.png',vSrc:'[SKIN]separator.png',size:25});	
}

NToolbarManager.prototype.init = function() {

}

NToolbarManager.prototype.destroy = function() {

}

/*** This method sets the toolbar ***/
NToolbarManager.prototype.setToolbar = function(toolbar) {    
	var active_toolstrip = [];
	
	if (toolbar) {
		if (!toolbar.isAdded) {
			this.toolstrip.push(toolbar);
			toolbar.isAdded = true;
		}
		active_toolstrip = active_toolstrip.concat(toolbar.getTools());
		
		var tid = toolbar.id;
	} else {
		var tid = -1;
	}
	this.screenToolstrip.removeMembers(this.screenToolstrip.getMembers());
	this.screenToolstrip.addMembers(active_toolstrip);	
}