/****************************************************************************/
/**** description: 	The ConsoleLogger sets the logging on the console  		*/
/****************************************************************************/

try {
    var console = console || {};
    console.log = console.log || function() {} ;
} catch (e)	{}
			
setLoadMessage = function (message) {
	var loadMessage = document.getElementById('load');
	if (loadMessage) {
		loadMessage.innerHTML=message;
	}
	console.log(message);
}
removeLoadMessage = function() {
	var loadMessage = document.getElementById('load');
	//loadWindow.close();
	if (loadMessage) {
		document.body.removeChild(loadMessage);
	}
	console.log("scripts geladen. Verwijder laadscherm");
}

function onResize(){
if (typeof(infoWindowManager)!= 'undefined')
    		{
    		infoWindowManager.repositionWindow();
    		}
}
