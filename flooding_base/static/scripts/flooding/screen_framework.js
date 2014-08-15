//  Global settings for all components in this application
isc.setAutoDraw(false);

/*** Screen: top ***/
console.log("Scherm opbouwen...");

isc.Img.create({
    ID: "scLogo",
    src: flooding_config.static_url+'images/lizard3/lizard_logo.png',
    overflow: "hidden",
    align: "center",
    width: 280,
    height: 45,
    autoDraw: false
});

isc.HLayout.create({
    ID: "scLogoCanvas",
    align: "left",
    overflow: "hidden",
    members:[
        scLogo
    ],
    width: 314,
    showResizeBar: false,
    autoDraw: false
});

isc.Canvas.create({
    ID: "scHeader",
    contents: "<div id=\"appHeaderPane\"></div>",
    align: "left",
    overflow: "hidden",
    width: "*",
    showResizeBar: false,
    autoDraw: false
});

isc.Canvas.create({
    ID: "scUser",
    contents: flooding_config.user_block_contents,
    width: "300px",
    align: "right",
    overflow: "hidden",
    showResizeBar: false,
    autoDraw: false
});

isc.Canvas.create({
    ID: "scNavigationToolbar",
    align: "center",
    overflow: "hidden",
    width: "340",
    height:"26",
    showResizeBar: false,
    backgroundColor: "red",
    autoDraw: false
});

/*** Navigation: left ***/
isc.TabSet.create({
    ID:"scNavigation",
    tabBarPosition: "bottom",
    tabBarAlign: "left",
    destroyPanes:"true",
    symmetricEdges:false,
    canCloseTabs:false,
    showResizeBar: false,
    showPaneContainerEdges:false,
    showTabPicker:false,
    width: 340,
    height: "100%",
    overflow:"hidden",
    animateMembers:true,
    animateMemberTime:100,
    closeClick : function(tab) { // doet het niet:
        console.log('close tab');
        this.removeTab(tab);
        if (tab.app) {
            tab.app.scNavigation.isAdded = false;
            console.log('close tab');
        }
    },
    autoDraw:true
});

scNavigation.tabBar.setHeight(0);

isc.Canvas.create({
    ID: "scSubApps",
    contents: "<div id=\"subAppHeaderPane\"></div>",
    overflow: "hidden",
    width: "370",
    height:"26",
    showResizeBar: false,
    autoDraw: false
});

/*** Screen: main ***/
// The element in the mainScreen where the buttons of the applications will be placed
isc.HLayout.create({
    ID:"scButtons",
    align: "right",
    overflow: "hidden",
    height: "26",
    width: "*",
    padding: 1,
    autoDraw:false
});

isc.Label.create({
    ID: "copyrightLabel",
    height: 26,
    width: '100%',
    //padding: 0,
    align: "center",
    valign: "center",
    wrap: false,
    showEdges: false,
    contents: "Copyright Nelen & Schuurmans - <a href='http://www.nelen-schuurmans.nl' target='_blank'>www.nelen-schuurmans.nl</a>"
});


mainScreenManager = new NMainScreenManager(null,{
    customLayers: custom_layers,
    useGoogleLayers: flooding_config.use_googlemaps,
    useOpenStreetMap: flooding_config.use_openstreetmaps,
    restrictMap: flooding_config.restrictmap,
    extent: flooding_config.extent
});

isc.Canvas.create({
    ID: "languageBin",
    showEdges: false,
    width:16, height:12
})

isc.Img.create({
    ID:"languageBut",
    width:16, height:12, top: 4,
    src:"/static_media/images/language_" + flooding_config.next_language + ".gif",
    showEdges:false,
    parentElement: languageBin,
    click: function() {
	isc.RPCManager.sendRequest(
	{
	    actionURL: "/i18n/setlang/",
	    httpMethod: "POST",
	    params: {"language": flooding_config.next_language,
		     "next": '/'},
	    callback: function() {window.location = ".";},
	    dataFormat: "json",
	    useSimpleHttp: true
	})
    }
})

/*** Creating total screen layout ***/
isc.VLayout.create({
    ID: "scPage",
    padding: "5px",
    width: "100%",
    height: "100%",
    overflow: "hidden",
    autoDraw: true,
    styleName:"imageheader",
    members: [
        isc.HLayout.create({
            ID: "topScreen",
            height: "57px",
            overflow: "hidden",
            members: [scLogoCanvas, scHeader, scUser, languageBin],
            autoDraw: false
        }),
        isc.HLayout.create({
            ID: "subAppToolbarPane",
            height: "26px",
            overflow: "hidden",
            members : [scSubApps, scButtons],
            backgroundImage: flooding_config.static_url + "images/lizard3/balk_.png",
            backgroundRepeat: "repeat-x",
            autoDraw: false
        }),
        isc.HLayout.create({
            ID: 'scMain',
            overflow: "hidden",
            members: [scNavigation,
                      isc.VLayout.create({
                          overflow: "hidden",
                          members: [isc.VLayout.create({ID:"scMainPage",width: "100%",height: "100%",overflow: "hidden", members: mainScreenManager.getScreens() })],
                          autoDraw: false
                      })],
            autoDraw: false
        }),

        isc.HLayout.create({
            ID: 'scBottomPane',
            overflow: "hidden",
            height: 26,
            members: [copyrightLabel],
            align: "center",
            backgroundImage: flooding_config.static_url + "images/lizard3/balk_.png",
            backgroundRepeat: "repeat-x",
            autoDraw: false
        })

    ]
});
mainScreenManager.mainPane = scMainPage;
mainScreenManager.isinit = true;
