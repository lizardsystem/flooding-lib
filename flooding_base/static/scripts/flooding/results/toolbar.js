console.log('start laden flooding/result/toolbar ...');

doneWarningIE = false;

if (!isc.Browser.isIE) {
    doneWarningIE = true;
}

floodingFilterResults = "all_with_results";


function frToolbarSettings() {

    isc.DynamicForm.create({
        ID: "formTypeResults",
        width: 200,
        fields: [{
            ID: 'selectResultType',
            name: "selectResult",
            title: ST_RESULT,
            type: "select",
            defaultValue:"all_with_results",
            valueMap: {
                all_with_results: ST_ALL_WITH_RESULTS,
                accepted: ST_ACCEPTED,
                rejected: ST_REJECTED,
                verify: ST_VERIFY,
                all: ST_ALL,
                archive: ST_ARCHIVE
            },
            change: function(form, item, value){
                floodingFilterResults = value;
                var region = getSelectedRegion();
                if (region!=null && region.isregion == true)
                    frBlockBreaches.tree.fetchData(
                        {region_id:region.rid, filter:floodingFilterResults},
                        function(dsResponse, data, dsRequest) {
                            frbreachLayer.refreshByData(data);
                            frbreachLayer.show();
                        });//teken punten via callback (na het laden)
                clear_scenarios();
            }
        }],
        autoDraw:false
    });

    isc.IButton.create({
        ID: "buttonExporteer",
        title: ST_EXPORT,
        showRollOver: false,
        showDown: true,
        showFocused: false,
        disabled:true,
        width: 120,
        click: function(form, item){
            scenario = getSelectedScenario()
            if (scenario) {
                window.open(locationFloodingData +
                            '?action=get_raw_result_scenario&scenarioid=' +
                            scenario.sid);
            }
        },
        autoDraw: false
    });

    isc.Slider.create({
        ID: "sliderOpacity",
        vertical: false,
        width: "190px",
        minValue: 0,
        maxValue: 100,
        numValues: 21,
        value:100,
        showRange: false,
        showTitle: true,
        disabled:true,
        //showValue: true,
        labelHeight:11,
        labelSpacing:0,
        height:20,
        title: ST_OPACITY,
        valueChanged : function (value) {
            if ((value<100) && !doneWarningIE) {
                alert("Waarschuwing:\nHet doorzichtig maken van de kaartlagen," +
                      "in combinatie met het ver ingezoomd zijn, neemt bij gebruik " +
                      "van Internet Explorer (erg) veel geheugen in. Aangeraden " +
                      "wordt om niet te ver in te zoomen of een andere browser te gebruiken" );
                doneWarningIE = true;
                sliderOpacity.setValue(100);
            } else {
                if (appManager.selectedApp.overlayManager) {
                    appManager.selectedApp.overlayManager.setOpacity(value / 100);
                }
            }
        }
    });

    isc.IButton.create({
        ID: "btSearch",
        title: "",
        autoFit: true,
        icon: "/static_media/Isomorphic_NenS_skin/images/actions/find.png",
        //radioGroup: "views",
        //actionType: "checkbox",
        click : function () {
            searchWindow.show();
        }
    });

    return {
        name: "flooding resulttools",
        tools: [
            btSearch,
            formTypeResults,
            sliderOpacity,
            buttonExporteer
        ]
    };
}

console.log('klaar laden flooding/result/toolbar ...');

