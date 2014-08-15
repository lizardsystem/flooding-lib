
intervalFormatter = function(value, shortNotation) {
    if (shortNotation == null) { var shortNotation = false }
    if (value == null) { var value = this }
    if (value.getUTCMinutes == null) { value = intervalReader(value)   }

    var p = "";
    //als negatief, maak positief
    if (value.valueOf()<0) {
        value = new Date( -value.valueOf());
        p = "-";
    }
    
    var month=value.getUTCMonth();
    var m=value.getUTCMinutes();
    var h=value.getUTCHours();
    var d=value.getUTCDate() - 1 + month2Days(month);

    if(m<10) m='0'+m;

    if (shortNotation) {
        if(h<10) h='0'+h;
	return p + d + ' d '+ h + ":" + m ;
    } else {
	return p + d + ' d '+ h + ":" + m ;//+ " uur"
    }
}

intervalReader = function(value) {//transformInput
    var unixDate = Date.UTC(1970,0,1,0,0,0);
    if (value == null) {
    	return new Date(unixDate);
    } else if (typeof(value) == "object") {
    	//Date object
    	return value;
    } else if (Number(value).stringify() != "NaN") {	
    	//in days
    	var d = new Date(Number(value)*24*60*60*1000);
	//d.setTime(parseInt(value)*24*60*60*1000);
	return d;
    } else if (typeof(value) == "string") { 
	value = value.toString();
	var days = (value.match(/^-?\d*\s(?!\:)/) * 1) || 0;
	if (days < 0) {
	    days *= -1;
	}
	var hours = (value.match(/(\d*)\:/));
	if (hours!=null) {hours = hours[1] * 1} else {hours = 0}
	var minutes = (value.match(/\:(\d*)/));
	if (minutes!=null) {minutes = minutes[1] * 1} else {minutes = 0}
	var milliseconds = ((days*24 + hours)*60 + minutes)*60*1000;
	var newDate = null;
	if (value.match(/^-/)) {
	    newDate = new Date(-(milliseconds).valueOf());
	    return newDate;
	} else {
	    newDate = new Date(milliseconds);
	    return newDate;
	}
    }
}


month2Days = function(monthAmount) {
    var monthDays = new Array(31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
    var days = 0;
    if (typeof(monthAmount) != "number") {
	return days;
    }
   
   for (i = 0; i < monthAmount && monthAmount < monthDays.length; i++) {
       days += monthDays[i];
   }     
    return days;
}