console.log('Loading iconSet ...')

/****************************************************************************/
/**** description: 	loads the icons that are used in the application        */
/****************************************************************************/
icons = {}
try {
    console.log('setting size');
    var size = new OpenLayers.Size(16,16);
    console.log('setting offset');
    var offset = new OpenLayers.Pixel(-(size.w/2), -size.h/2);

    icons["doorbraak2"] = new OpenLayers.Icon( "http://maps.google.com/mapfiles/kml/pal4/icon25.png",size,offset);
    icons["brug"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconBrugZW.png",size,offset);
    icons["rondje"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconRWZIZW.png",size,offset);
    icons["circlered"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconCircleRed.png",size,offset);
    icons["circlegreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconCircleGreen.png", size,offset);
    icons["circleyellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconCircleYellow.png", size,offset);

    icons["square"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSquareZW.png",size,offset);
    icons["squarered"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSquareRed.png",size,offset);
    icons["squaregreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSquareGreen.png", size,offset);
    icons["squareyellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSquareYellow.png", size,offset);

    icons["bridge"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconBrugZW.png",size,offset);
    icons["bridgered"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconBrugRed.png",size,offset);
    icons["bridgegreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconBrugGreen.png", size,offset);
    icons["bridgeyellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconBrugYellow.png", size,offset);

    icons["weir"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconStuwZW.png",size,offset);
    icons["weirred"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconStuwRed.png",size,offset);
    icons["weirgreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconStuwGreen.png", size,offset);
    icons["weiryellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconStuwYellow.png", size,offset);

    icons["culvert"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconDuikerZW.png",size,offset);
    icons["culvertred"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconDuikerRed.png",size,offset);
    icons["culvertgreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconDuikerGreen.png", size,offset);
    icons["culvertyellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconDuikerYellow.png", size,offset);

    icons["sluis"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSluisZW.png",size,offset);
    icons["sluisred"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSluisRed.png",size,offset);
    icons["sluisgreen"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSluisGreen.png", size,offset);
    icons["sluisyellow"] = new OpenLayers.Icon( flooding_config.root_url + "static_media/images/icons/LizardIconSluisYellow.png", size,offset);

    console.log('return icons')
}
catch (e) { console.log(e);}
