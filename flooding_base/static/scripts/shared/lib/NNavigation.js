console.log('loading NNavigation ...')

/********************************************************************/
/**** class: 		NNavigation   			            	        */
/**** description: 	This class is responsible for showing the       */
/****               navigation of the selected application, which   */ 
/****               is shown at the left side of the screen.        */
/****               It can contain multiple blocks (NBlock).        */
/********************************************************************/

function NNavigation(options) {
    options = options || {};

    this.id = "navigation" + Nget_id();
    this.name = options.name || "-";
    this.initFunction = options.initFunction || null;
        
    this.isInit = false;
    this.isAdded = false;
    this.tab = null;
    this.tabset = null

}

/**** Initializes the NNAvigation ****/
NNavigation.prototype.init = function() {
	if (this.isInit) {
		return;
	}
	
	this.tab = {
        ID: "Tab"+this.id,
        canClose:false,
        title: this.name,
        pane: eval(this.initFunction+"()")
    }	
	this.isInit = true;
}


NNavigation.prototype.addToTabSet = function(tabset) {
    console.log('entering method: "addToTabSet" with "tabset"='+tabset)
	if (!this.isInit) {
		console.log("navigation " + this.name+ " is not initialised")
		return;
	}
	
	if (this.isAdded) {
		return;
	}
	
	this.tabset = tabset;
    this.tabset.addTab(this.tab);
	this.isAdded = true;
}

/**** Shows the navigation sidebar ****/
NNavigation.prototype.show = function() {
	if (!this.isInit || !this.isAdded) {
		console.log("navigation " + this.name+ " is not initialised or added to tabset");
		return;
	}
	
	this.tabset.show();
	this.tabset.selectTab(this.tab);
}

NNavigation.prototype.destroy = function() {

}

console.log('loaded NNavigation successfully')