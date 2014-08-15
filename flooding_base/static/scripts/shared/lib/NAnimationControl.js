console.log('loading NAnimationControl ...');

/**********************************************************************/
/**** class:         NAnimationControl                                  */
/**** description:     This class is responsible for the control           */
/****                that is used to give commands for the animation.  */
/**********************************************************************/

function NAnimationControl( _map, overlayManager,options ) {
    options = options || {};
    this.om = overlayManager;
    this._map = _map;
    this.smartClientScreen = options.smartClientScreen || scMap;
    this.defaultInterval = options.interval || 1000;
    this.interval = this.defaultInterval;
    this.img = null;
    this.playState = 0;
    this.frameNr = 0;
    this.playInterval = null;
    this._visible = false;
    //lege zaken
    this.activeOverlay = null;
    this.currentSpeed = 1;
    this.maxSpeed = 4;
    this.minSpeed = 1;

    //omdat de control niet togevoegd wordt via map.addControl(), wordt hier 'handmatig' deze functie aangeroepen
    this.initialize();
}

NAnimationControl.prototype._funcScAnimationControl = function(oMan) {

    /***************animation slider: must come first because other components use this one****/
    isc.Slider.create({
        ID: "acSlider",
        vertical: false,
        width: "100%",
        minValue: 0,
        maxValue: 49,
        numValues: 50,
        showRange: true,
        showTitle: false,
        showValue: true,
        labelHeight:13,
        labelSpacing:1,
        height:40,
        roundValues:true,
        title: "Frame",
        valueChanged : function (value) {
            if (!this.valueIsChanging()) {
                if (typeof(appManager) != 'undefined') {
                    appManager.selectedApp.overlayManager.animationControl._showFrame(value);
                }
            }
        }
    });

    isc.Label.create({
        ID: "scTimeDisplay",
        height: "15px",
        align: "center",
        contents: "-",
        autoDraw:false
    });


    isc.IButton.create({
        ID: "scButtonAniBegin",
        title: "|<",
        width: 35,
        showRollOver: false,
        actionType: "button",
        showFocused:false,

        click: function () {
            appManager.selectedApp.overlayManager.animationControl.firstFrame();
        }
    });

    isc.IButton.create({
        ID: "scButtonAniPrevious",
        title: "<<",
        width: 35,
        showRollOver: false,
        actionType: "button",
        showFocused:false,
        click: function () {
            appManager.selectedApp.overlayManager.animationControl.previousFrame();
        }
    });

    isc.IButton.create({
        ID: "scButtonAniPlay",
        title: ">",
        width: 35,
        showRollOver: false,
        actionType: "checkbox",
        showDown:true,
        showFocused:false,
        click: function () {
            if (this.isSelected()) {
                this.setTitle("||");
                appManager.selectedApp.overlayManager.animationControl._play();
            } else {
                this.setTitle(">");
                appManager.selectedApp.overlayManager.animationControl._stop();
            }
        }
    });

    isc.IButton.create({
        ID: "scButtonAniNext",
        title: ">>",
        showDown:true,
        showRollOver: false,
        actionType: "button",
        showFocused:false,
        width: 35,
        click: function () {
            appManager.selectedApp.overlayManager.animationControl.nextFrame();
        }
    });

    isc.IButton.create({
        ID: "scButtonAniEnd",
        title: ">|",
        showRollOver: false,
        actionType: "button",
        showFocused:false,
        width: 35,
        click: function () {
            appManager.selectedApp.overlayManager.animationControl.lastFrame();
        }
    });

    isc.IButton.create({
        ID: "scButtonAniSpeed",
        title: "x2",
        showRollOver: false,
        actionType: "button",
        showFocused:false,
        width: 35,
        click: function () {
            var currentSpeed = appManager.selectedApp.overlayManager.animationControl.currentSpeed;
            var maxSpeed = appManager.selectedApp.overlayManager.animationControl.maxSpeed;
            var minSpeed = appManager.selectedApp.overlayManager.animationControl.minSpeed;
            var interval = appManager.selectedApp.overlayManager.animationControl.interval;

            if (currentSpeed == 1) {
                scButtonAniSpeed.setTitle("x4");
                currentSpeed *= 2;
                interval = interval / 2;
            } else if (currentSpeed == 2) {
                scButtonAniSpeed.setTitle("x1");
                currentSpeed *= 2;
                interval = interval / 2;
            } else if (currentSpeed == 4 ){
                scButtonAniSpeed.setTitle("x2");
                currentSpeed = minSpeed;
                interval = appManager.selectedApp.overlayManager.animationControl.defaultInterval;
            }

            this.redraw();
            appManager.selectedApp.overlayManager.animationControl.currentSpeed = currentSpeed;
            appManager.selectedApp.overlayManager.animationControl.interval = interval;
        }
    });

    isc.HLayout.create({
        ID:"scAniButtons",
        //align: "center",
        overflow: "hidden",
        height: "24px",
        width:"100%",
        membersMargin: 5,

        //border: "1px solid blue",
        members: [
            scButtonAniBegin,
            scButtonAniPrevious,
            scButtonAniPlay,
            scButtonAniNext,
            scButtonAniEnd,
            scButtonAniSpeed,
            scTimeDisplay
        ],
        showResizeBar: false,
        autoDraw:false
    });

    isc.VLayout.create({
        ID: "scAnimationPane",
        width:"100%",
        //membersMargin: 5,
        padding:5,
        overflow: "hidden",
        members: [
            scAniButtons,
            acSlider
        ]
    });

    isc.Canvas.create({
        ID:"scAnimationControl",
        left:80, top:7,width:320, height:85,
        backgroundColor:"white",
        opacity:85,
        border: "1px solid grey",
        //contents:"Drag Me",
        canDragReposition:true,
        dragAppearance:"target",

        //keepInParentRect: true, TO DO: instelbaar maken

        showShadow: true,
        shadowSoftness: 5,
        shadowOffset: 4,

        //showDragShadow:true,
        // dragShadowDepth:10,

        animateHideTime:500,
        animateFadeTime:500,
        animateShowTime:500,

        overflow: "hidden"
        //autoDraw:true
    });

    scAnimationControl.addChild(scAnimationPane);
};

/**************** standaard control functies ***************/

NAnimationControl.prototype.initialize = function(map) {
    //voeg de control toe direct aan het smartclient mapframe
    this._funcScAnimationControl(this);
    scAnimationControl.hide();
    this.smartClientScreen.addChild(scAnimationControl);
};

/**************** standaard control functies ***************/

NAnimationControl.prototype.hide = function() {
    //stop de animatie
    this.stop();
    //geef aan sc door om te verbergen (gebruik makend van animatie)
    scAnimationControl.animateHide("fade");
    this._visible = false;
};

NAnimationControl.prototype.show= function(show_play) {
    //geef aan sc door om te laten zien (gebruik makend van animatie)

    scAnimationControl.animateShow("fade");
    this._visible = true;
};

NAnimationControl.prototype.remove = function() {
    //to do
    alert('test');
    this.smartClientScreen.removeChild(scAnimationControl);
    scAnimationControl.animateHide("fade");
    this._visible = false;

};

NAnimationControl.prototype.visible = function() {
    return this._visible;
};

/**************** basis functies ***************/

NAnimationControl.prototype.timestep = function() { return this.frameNr; };

NAnimationControl.prototype.initOverlay = function(overlay) {
    //zet de huidige animatie stil
    this.stop();


    // zet de actieve overlay en laadt de plaatjes
    this.activeOverlay = overlay;

    if (this.activeOverlay.type == ANIMATEDWMSOVERLAY) {
        scButtonAniPlay.hide();
    } else {
        scButtonAniPlay.show();
    }

    //zet de slider goed
    acSlider.minValue = this.activeOverlay.animation.display_firstnr * this.activeOverlay.animation.delta/3600;
    if (this.activeOverlay.animation.firstlabel) {
        acSlider.minValueLabel = this.activeOverlay.animation.firstlabel;
    } else {
        acSlider.minValueLabel = acSlider.minValue.toFixed(1) + ' ' + ST_HOUR;
    }

    acSlider.maxValue = (this.activeOverlay.animation.display_lastnr) * this.activeOverlay.animation.delta/3600;
    if (this.activeOverlay.animation.lastlabel) {
        acSlider.maxValueLabel = this.activeOverlay.animation.lastlabel;
    } else {
        acSlider.maxValueLabel = acSlider.maxValue.toFixed(1) + ' ' + ST_HOUR;
    }

    if (this.activeOverlay.animation.showDateLabel) {
        scTimeDisplay.show();
    } else {
        scTimeDisplay.hide();
    }

    acSlider.showValue = this.activeOverlay.animation.showValue;

    acSlider.numValues = this.activeOverlay.animation.display_lastnr - this.activeOverlay.animation.display_firstnr;

    this.firstFrame();
    //redraw labels


    //zet de slider op de laatst actieve stand van vorige scenario (kan korter zijn)
    if (this.timestep() > this.activeOverlay.animation.display_lastnr) {
        this.lastFrame();
    } else {
        //aangezien de value van de slider niet veranderd wordt het overstromings beeld zo vernieuwd
        this._showFrame( this.timestep() );
    }
    acSlider.initWidget();
    //to als instellingen remember last state, dan bovenstaande, anders first frame
    //this.firstFrame();
    //this.activeOverlay.preLoad(this.activeOverlay.animation.firstnr);

};

NAnimationControl.prototype.getFrameNr = function(display_nr) {
    if (this.activeOverlay) {
        return Math.round(display_nr * 3600 / this.activeOverlay.animation.delta) - this.activeOverlay.animation.display_firstnr;
    } else {
        return 0;
    }
};

NAnimationControl.prototype._showFrame = function(i) {
    this.displayFrameNr = i;
    this.om.showOverlay(this.getFrameNr(i));
    if (this.activeOverlay.animation.label_function) {
        this.activeOverlay.animation.label_function(i, this.activeOverlay, scTimeDisplay);
    }


};

NAnimationControl.prototype.showFrame = function(i) {
    acSlider.setValue(i);
};

NAnimationControl.prototype.setInterval = function(interval) {
    this.interval = interval;
};

NAnimationControl.prototype.getInterval = function(interval) {
    return this.interval;
};


/**************** afspeel functies ***************/
//functies apart, zodat ze ook door het programma aangeroepen kunnen worden

NAnimationControl.prototype._play = function() {
    var oMan = this;
    this.playState = 1;
    this.playInterval = window.setTimeout(function() { oMan._playing(); },this.interval);
};

NAnimationControl.prototype._stop = function() {
    //zet op 0, signaal wordt na het aflopen van het vorige interval opgepikt
    //TO DO: nadenken over veranderen figuur knop
    this.playState = 0;
    window.clearInterval(this.playInterval);
};

NAnimationControl.prototype.play = function() {
    if (!scButtonAniPlay.isSelected()) {
        scButtonAniPlay.select();
        scButtonAniPlay.click();
    }
};

NAnimationControl.prototype.stop = function() {
    if (scButtonAniPlay.isSelected()) {
        scButtonAniPlay.deselect();
        scButtonAniPlay.click();
    }
    this.playState = 0;
    window.clearInterval(this.playInterval);
};

//functie die zorgt voor het afspelen
NAnimationControl.prototype._playing = function() {
    //nog niet gestopt en noog niet aan het einde
    var oMan = this;


    if ((this.playState == 1) && (this.displayFrameNr < (this.activeOverlay.animation.display_lastnr)))
    {
        if (this.activeOverlay.animation.autostopatend && (this.displayFrameNr == this.activeOverlay.animation.display_lastnr-1)) {
            this.stop();
        }
        //no interval but first advance and then set timeout again for smooth animations in case advance takes longer
        this.advance();
        this.playInterval = window.setTimeout(function() { oMan._playing(); },this.interval);
    } else {
        //change button
        if (this.playState == 1 && this.activeOverlay.animation.autorewind) {
            this.startFrame();
            this.playInterval = window.setTimeout(function() { oMan._playing(); },this.interval);
        } else {
            this.stop();
        }
    }
};

NAnimationControl.prototype.firstFrame = function() {
    this.stop();
    if (this.displayFrameNr > 0 ) {
        this.startFrame();
    } else {
        this.showFrame(this.activeOverlay.animation.display_firstnr);
    }
    //acSlider.initWidget();
};

NAnimationControl.prototype.startFrame = function() {
    this.showFrame(0);
    //acSlider.initWidget();
};

NAnimationControl.prototype.lastFrame = function() {
    this.stop();
    this.showFrame(this.activeOverlay.animation.display_lastnr);
    //acSlider.initWidget();
};

NAnimationControl.prototype.nextFrame = function() {
    this.stop();
    this.advance();
};

NAnimationControl.prototype.previousFrame = function() {
    this.stop();
    if (this.displayFrameNr >= 1) {
        this.showFrame(this.displayFrameNr - 1);
    }
};

NAnimationControl.prototype.advance = function() {
    if (this.displayFrameNr < (this.activeOverlay.animation.display_lastnr)) {
        this.showFrame(this.displayFrameNr + 1 );
        return true;
    } else {
        return false;
    }
};
