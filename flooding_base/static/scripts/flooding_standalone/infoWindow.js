
function frInfoWindowSettings() {

    iwScenarioInformation = new NInfoWindow("Scenario Informatie",{
        
        tabName: 'Info' ,
		defaultSize : {width: 100, height:400 },
		canClose: false,
		canMax: false,
		canMin: false,
		showTitle: true,
		preLoad:false,
		
		isForm:true,
		url:"/flooding/infowindow/1/information/",
		params:{scenario:1,action:'information'},
		type: HTMLPANE,
		
     
    });
    
}