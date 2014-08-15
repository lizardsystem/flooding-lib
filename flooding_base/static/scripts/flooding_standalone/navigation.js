/***************** functions **********************/
var selectedScenarioId = null;
var selectedRegionId = null;
var filterResults = "all";

function stgetScenarioId() {
    return selectedScenarioId;
}

function stgetRegionId() {
    return selectedRegionId;
}

function stclear_breaches() {
    stbreachLayer.clearAll();
    stBlockBreaches.setLabel();
    overlayManager.clearAllOverlays();
    overlayManager.hide();

    //sliderOpacity.setDisabled(true);
}



/******************** blocks **********************/
function stNavigation() {
	d = isc.Tree.create({
        modelType: "parent",
        nameProperty: "name",
        data: sa_data
        })
	
	stBlockRegions = new NBlock("regios","regio",
	{
	    
	    fields:[
	        {name:"id", primaryKey:true, hidden:true, type:"text"},
	        {name:"name", type:"text" },
	        {name:"north" , type:"integer"},
	        {name:"south" , type:"integer"},
	        {name:"west" , type:"integer"},
	        {name:"east" , type:"integer"}
	    ],

	}, {
	    data:d,
	    emptyMessage:"-",
	    leafClick: function(viewer,leaf,recordNum){
			//niet echt juiste palek, maar het werkt
			overlayManager.setOpacity(0.75);
			
			
			stclear_breaches();
	        stBlockRegions.setLabel(leaf.name);
	        stBlockBreaches.tree.setData(
	        	isc.Tree.create({
        			modelType: "parent",
        			nameProperty: "name",
        			data:leaf.breaches
        		})
        	);

        	stbreachLayer.refreshByData(leaf.breaches);
	        stbreachLayer.show();

	        Ozoom(map ,leaf );
	    },
	});
	
	stBlockBreaches = new NBlock("doorbraaklocaties","doorbraaklocatie",
	{
	    dataURL:locationFloodingData,
	    fields:[
	        {name:"id", primaryKey:true, hidden:true, type:"text"},
	        {name:"name", type:"text" },
	        {name:"x" , type:"integer"},
	        {name:"y" , type:"integer"},
	        {name:"pngloc",type:"text"},
	        {name:"firstnr" , type:"integer"},
	        {name:"lastnr" , type:"integer"},
	    ]
	},{
	    emptyMessage:"Kies een gebied" ,
	    leafClick: function(viewer,leaf,recordNum){
	        overlayManager.clearAllOverlays();
	        stBlockBreaches.setLabel(leaf.name);
	        stbreachLayer.select(leaf.id,false);
	        
	        leaf.start_nr = leaf.start_nr || 38;
	        leaf.dt = leaf.dt || 3600;
	        leaf.projection = 28992;

			//gegevens hierin nog aanpassen op fetch vanuit files. Testen!!!!!
			if (!overlayManager.setActiveOverlay(leaf.id)) {			
	        	var layer = null;			
				layer = new NAnimatedMapOverlay(leaf.id, leaf.name, {
					frameUrl: 'presentation' + leaf.loc,
					bounds: leaf ,
					size: {width: leaf.width, height: leaf.height},
					animation: new NAnimation(leaf.first_nr, leaf.last_nr, {startnr: leaf.start_nr, autoplay: true, autorewind: true, dt:3600, autostopatend: true } )
				});
				overlayManager.addAndSetActiveOverlay(layer);
			}
		        
	         //sliderOpacity.setDisabled(false);   
	        
	    }
	});
	
    /*options = options || {};
    this.getSettingsFromPgw = options.getSettingsFromPgw || false;
    this.getSettingsFromRequest = options.getSettingsFromRequest || false;
    this.settingsRequestUrl = options.settingsRequestUrl || null;
    this.settingsRequestParams = options.settingsRequestParams || {};
    
    this.framesFromRequest = options.animationFromRequest || true;
    this.frameUrl = options.frameUrl || null;
    this.framesRequestParams = options.framesRequestParams || {};
    
    this.rawResultUrl = options.rawResultUrl || null;
    
    
    //settings which can also be get from pgw // request
    this.bounds = options.bounds || null;
    this.size = options.size || null;
    if (this.size) {
    	this.pictureSize(this.size.width, this.size.height);
    }*/

	
	//stBlockRegions.tree.setData(d);
	
	/******************** screen **********************/
	
	isc.VLayout.create({
	    ID:"floodingStandaloneResultNavigation",
	    membersMargin: 5,
	    width: "100%", height: "100%", overflow:"hidden",
	    members: [
	        isc.VLayout.create({ height:"30%", members: stBlockRegions.getMembers(),    autoDraw:false}),
	        isc.VLayout.create({ height:"70%", members: stBlockBreaches.getMembers(),   autoDraw:false})
	    ],
	    autoDraw:false
	});
	
	return floodingStandaloneResultNavigation;
}



