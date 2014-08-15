console.log('loading NInfoWindowManager.js ...')

/************************************************************/
/**** class: 		NInfoWindowManager   				    */
/**** description: 	This class is responsible for showing   */
/****               the NInfoWindowContainers       		*/
/************************************************************/

function NInfoWindowManager(name, parentScreen, options) {   

    this.name = name;
    this.parentScreen = parentScreen;
   
    options = options || {}
    this.shortname = options.shortname || name;    
    this.offset = options.offset || {top:10, bottom: 10, right: 10, left:10};
    this.clipOffset = options.clipOffset ||   {top:40, bottom: 40, right: 40, left:40};    
    this.isMaximized = options.isMaximized || true;   
    this.pre_init();    
    this.currentWindows = [];
}

NInfoWindowManager.prototype.pre_init = function() {
    console.log('entering method "pre_init"')
    isc.TabSet.create({
        ID:"tabSetInfoWindow",
        tabBarPosition: "bottom",
        symmetricEdges:false,
        tabs:[],
        width:'100%', height:'100%',
        backgroundColor:"white", //opacity:100,
        paneContainerOverflow:"hidden",
        autoDraw:false
    });

    isc.Canvas.create({
	ID:"informationWindow",
            left:800, top:200, width:400,
	dragAppearance:"target",
	canDragResize:true,        
	keepInParentRect: true,
	animateHideTime:500,
	animateFadeTime:500,
	animateShowTime:500,
	overflow: "hidden",
	autoDraw:false,
	snapTo: "BR"                        
    });
           
    isc.Button.create({
	    ID: "resizeButton",	    	    
	    border: "1px solid black",
	    backgroundColor: "white",
	    showRollOver: false,
	    showDown: true,
	    showFocused: false,
	    align:'center',
	    parentResized: function () {     	
        	this.moveTo(this.parentElement.getWidth() - 30 - this.width , this.top);
        },
	    top:5,
	    width: 15,
	    height:15,
	    click: "infoWindowManager.resizeWindow()",
	    autoDraw: false
	});	
	
	this.tabSet = tabSetInfoWindow;
    this.screen = informationWindow;
    this.resizeButton = resizeButton;
   
    // resize window to maximze, therefor do as if windows not yet has the maximized setting:
    this.oldHeight = 300;
    this.oldWidth = 420;
	this.isMaximized = !this.isMaximized;	
	this.resizeWindow(null, null);
	
    this.screen.addChild(tabSetInfoWindow);    
 	this.screen.addChild(resizeButton);
 	resizeButton.bringToFront();
    this.setTabBarItemClickListener();                	
}

NInfoWindowManager.prototype.resizeWindow = function(form, item, width)
{
   console.log('isMaximized: ' +this.isMaximized);
   if(this.isMaximized)
   {   
       // minimize window              
       this.oldHeight = this.screen.getHeight();   
       this.oldWidth = this.screen.getWidth();    
       
       var nowBottom = this.screen.getBottom();
       var nowRight = this.screen.getRight();       
       var newHeight = 25;
       var newWidth = width || 420;
       
   	   this.screen.animateRect(nowRight - newWidth, nowBottom - newHeight, newWidth, newHeight);
       this.resizeButton.setTitle("<b>+</b>")
       this.isMaximized = false;
   }
   else
   {
        // maximize window
        var nowBottom = this.screen.getBottom();  
        var nowRight = this.screen.getRight()              
        var newHeight = this.oldHeight;   
        var newWidth = width || this.oldWidth;     
        
        
        this.screen.animateRect(nowRight-newWidth, nowBottom - newHeight , newWidth, newHeight);
        this.resizeButton.setTitle("<b>-</b>");
        this.isMaximized = true;        
   }
}

/**** Repositions the infowindow if it does not fit anymore in the new browser due to resizing.
      If the resizing does not have to effect on the position of the infowindow, the window will not move. ****/
NInfoWindowManager.prototype.repositionWindow = function() {
    var move = false;    
    var newTop = this.screen.getTop();
    var newLeft = this.screen.getLeft();
    
    var newBodyHeight = document.body.clientHeight;
    var newBodyWidth = document.body.clientWidth;    
        
    // Check if infowindow bottom is below the specified offset from the bottom of the screen
    if(this.screen.getBottom() > newBodyHeight - this.offset.bottom)
    {            
  		newTop = newBodyHeight - this.screen.getHeight() - this.offset.bottom;
  		move=true;
  		console.log('Repositioning: bottom is off the screen; newtop = ' + newTop);
    }    
    else if(this.oldBodyHeight - this.screen.getBottom()  < this.clipOffset.bottom)
    {
        // Check if the distance to the bottom is within the clip range               
    	newTop = newBodyHeight - this.screen.getHeight() - (this.oldBodyHeight - this.screen.getBottom());    	
  		move=true;
  		console.log('Repositioning: bottom clipped; newtop = ' + newTop);
    }
    
    // Check if infowindow right side is left from the specified offset from the right side of the screen
    if(this.screen.getRight() > newBodyWidth - this.offset.right)
    {
    	newLeft = newBodyWidth - this.screen.getWidth() - this.offset.right;
    	move=true;
    	console.log('Repositioning: right is off the screen; newLeft = ' + newLeft);
    }
    else if(this.oldBodyWidth - this.screen.getRight()  < this.clipOffset.right)
    {
    	// Check if the distance to the right side is within the clip range    	    	
        var newLeft = newBodyWidth- this.screen.getWidth() - (this.oldBodyWidth - this.screen.getRight());       
  		move=true;
  		console.log('Repositioning: right is clipped; newLeft = ' + newLeft);
    }    
        
  	if (this.screen.getTop() < this.offset.top)
    {
        newTop = this.offset.top;
    	move=true;
    	console.log('Repositioning: top off the screen; newTop = ' + newTop);
    }
  	if(this.screen.getLeft() < this.offset.left)
    {
    	newLeft = this.offset.left;
    	move=true;  
    	console.log('Repositioning: left off the screen; newLeft = ' + newLeft);
    }  
	if(move)
	{
	    newTop = (newTop < this.offset.top) ? this.offset.top : newTop;
	    newLeft = (newLeft < this.offset.left) ? this.offset.left : newLeft;	    
		this.screen.animateMove(newLeft,newTop,null,1000);
	}	
	this.oldBodyHeight =  newBodyHeight;
	this.oldBodyWidth = newBodyWidth;
}

NInfoWindowManager.prototype.init = function() {
    
}

NInfoWindowManager.prototype.destroy = function() {

}

/**** Links a function to the event when a tab of the TabBar of the infowindow is clicked. ****/
NInfoWindowManager.prototype.setTabBarItemClickListener = function() {
    console.log('entering method "itemClick" ')    
    tabSetInfoWindow.tabBar.itemClick =  function(item,itemNum)	{        
        var newSelectedInfoWindow = infoWindowManager.currentWindows[itemNum];
        newSelectedInfoWindow.reloadIfNeeded();
        if(!infoWindowManager.isMaximized)
        {            
            infoWindowManager.resizeWindow(null, null, newSelectedInfoWindow.defaultSize.width);            
        }
        else
        {        
             newSelectedInfoWindow.resize();
        }        
    }
}


/**** Sets InfoWindows in the 'InfoWindows-browser'         ****/
/**** With no parameters the current windows are set again. ****/  
NInfoWindowManager.prototype.setWindows = function(infoWindows) {
    console.log('entering method "setWindows"');
	//check if it is a container and get array with windows
	
	if (infoWindows && infoWindows.isContainer) {
		infoWindows = infoWindows.getInfoWindows();
	}	
	
	for (var i = 0; i < this.currentWindows.length; i++) {
	    this.tabSet.updateTab("tab_"+this.currentWindows[i].id, null);
		this.tabSet.removeTab("tab_"+this.currentWindows[i].id);
	}
	
	if (infoWindows) {
		this.currentWindows = infoWindows;
		for (var i = 0; i < infoWindows.length; i++) {		    
			    this.tabSet.addTab({title:infoWindows[i].tabName, ID:("tab_"+infoWindows[i].id), pane: infoWindows[i].pane, disabled:!infoWindows[i].enabled});			    
		}
	} 
	else 
	{
		this.currentWindows = [];
	}
	this.showWindowsIfNeeded();		
}


/**** Shows the infowindow if needed, i.e. if there is at least one tabpage to show. ****/
NInfoWindowManager.prototype.showWindowsIfNeeded = function (){    
	var atLeastOneEnabledWindows = false;
	
	for (var i = 0; i < this.currentWindows.length; i++) {
		    if(this.currentWindows[i].enabled)
		    {		
			   atLeastOneEnabledWindows = true;
			   break;
			}			
	}
	
	if (atLeastOneEnabledWindows) 
	{
		scPage.addChild(informationWindow, "", true );		
		this.currentWindows[0].resize();		
	}
	else
	{ 
	    scPage.removeChild(informationWindow);
	}
}

console.log('loaded NInfoWindowManager.js succesfully')