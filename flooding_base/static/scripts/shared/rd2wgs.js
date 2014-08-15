
// Conversion from RD to Wgs84 coordinates
function RDLatLong(x , y) {
	//trace +="\nRDLatLong";

	var x0  = 155000.000;
	var y0  = 463000.000;

	var f0 = 52.156160556;
	var l0 =  5.387638889;

	var a01=3236.0331637 ; var b10=5261.3028966;
	var a20= -32.5915821 ; var b11= 105.9780241;
	var a02=  -0.2472814 ; var b12=   2.4576469;
	var a21=  -0.8501341 ; var b30=  -0.8192156;
	var a03=  -0.0655238 ; var b31=  -0.0560092;
	var a22=  -0.0171137 ; var b13=   0.0560089;
	var a40=   0.0052771 ; var b32=  -0.0025614;
	var a23=  -0.0003859 ; var b14=   0.0012770;
	var a41=   0.0003314 ; var b50=   0.0002574;
	var a04=   0.0000371 ; var b33=  -0.0000973;
	var a42=   0.0000143 ; var b51=   0.0000293;
	var a24=  -0.0000090 ; var b15=   0.0000291;

	with(Math)
	{
		var dx=(x-x0)*pow(10,-5);
		var dy=(y-y0)*pow(10,-5);

		var df = a01*dy +  a20*pow(dx,2) +  a02*pow(dy,2) +  a21*pow(dx,2)*dy +  a03*pow(dy,3)
		df+= a40*pow(dx,4) +  a22*pow(dx,2)*pow(dy,2) +  a04*pow(dy,4) +  a41*pow(dx,4)*dy
		df+= a23*pow(dx,2)*pow(dy,3) +  a42*pow(dx,4)*pow(dy,2) +  a24*pow(dx,2)*pow(dy,4);
		var f = f0 + df/3600;

		var dl = b10*dx + b11*dx*dy + b30*pow(dx,3) +  b12*dx*pow(dy,2) +  b31*pow(dx,3)*dy;
		dl+= b13*dx*pow(dy,3)+ b50*pow(dx,5) +  b32*pow(dx,3)*pow(dy,2) +  b14*dx*pow(dy,4);
		dl+= b51*pow(dx,5)*dy + b33*pow(dx,3)*pow(dy,3) +  b15*dx*pow(dy,5);
		var l = l0 + dl/3600;

		//WGS84
		var fWgs= f + (-96.862 - 11.714 * (f-52)- 0.125 * (l-5)) / 100000;
		var lWgs= l + (-37.902 +  0.329 * (f-52)-14.667 * (l-5)) / 100000;
	}
	fWgs = Math.round(fWgs * 10000000) / 10000000;
	lWgs = Math.round(lWgs * 10000000) / 10000000;


	var x = fWgs;
	var y = lWgs;

	var pos = new GLatLng(fWgs, lWgs);
	return pos;
}

function ORDLonLat(x , y) {
	//trace +="\nRDLatLong";

	var x0  = 155000.000;
	var y0  = 463000.000;

	var f0 = 52.156160556;
	var l0 =  5.387638889;

	var a01=3236.0331637 ; var b10=5261.3028966;
	var a20= -32.5915821 ; var b11= 105.9780241;
	var a02=  -0.2472814 ; var b12=   2.4576469;
	var a21=  -0.8501341 ; var b30=  -0.8192156;
	var a03=  -0.0655238 ; var b31=  -0.0560092;
	var a22=  -0.0171137 ; var b13=   0.0560089;
	var a40=   0.0052771 ; var b32=  -0.0025614;
	var a23=  -0.0003859 ; var b14=   0.0012770;
	var a41=   0.0003314 ; var b50=   0.0002574;
	var a04=   0.0000371 ; var b33=  -0.0000973;
	var a42=   0.0000143 ; var b51=   0.0000293;
	var a24=  -0.0000090 ; var b15=   0.0000291;

	with(Math)
	{
		var dx=(x-x0)*pow(10,-5);
		var dy=(y-y0)*pow(10,-5);

		var df = a01*dy +  a20*pow(dx,2) +  a02*pow(dy,2) +  a21*pow(dx,2)*dy +  a03*pow(dy,3)
		df+= a40*pow(dx,4) +  a22*pow(dx,2)*pow(dy,2) +  a04*pow(dy,4) +  a41*pow(dx,4)*dy
		df+= a23*pow(dx,2)*pow(dy,3) +  a42*pow(dx,4)*pow(dy,2) +  a24*pow(dx,2)*pow(dy,4);
		var f = f0 + df/3600;

		var dl = b10*dx + b11*dx*dy + b30*pow(dx,3) +  b12*dx*pow(dy,2) +  b31*pow(dx,3)*dy;
		dl+= b13*dx*pow(dy,3)+ b50*pow(dx,5) +  b32*pow(dx,3)*pow(dy,2) +  b14*dx*pow(dy,4);
		dl+= b51*pow(dx,5)*dy + b33*pow(dx,3)*pow(dy,3) +  b15*dx*pow(dy,5);
		var l = l0 + dl/3600;

		//WGS84
		var fWgs= f + (-96.862 - 11.714 * (f-52)- 0.125 * (l-5)) / 100000;
		var lWgs= l + (-37.902 +  0.329 * (f-52)-14.667 * (l-5)) / 100000;
	}
	fWgs = Math.round(fWgs * 10000000) / 10000000;
	lWgs = Math.round(lWgs * 10000000) / 10000000;


	var x = fWgs;
	var y = lWgs;

	var pos = new OpenLayers.LonLat( lWgs, fWgs);
	return pos;
}


function wgs2rds(wgslat,wgslon)
{
   var rdx = wgs842rd_x(wgslat,wgslon);
   var rdy = wgs842rd_y(wgslat,wgslon);
   return {x:rdx,y:rdy};
}

function wgs842rd_x(lat1, lon1)
{
var lat2 = wgs842bessel_lat(lat1, lon1, 0);
var lon2 = wgs842bessel_lon(lat1, lon1, 0);

return bessel2rd_x(lat2, lon2);
}

function wgs842rd_y(lat1, lon1)
{
var lat2 = wgs842bessel_lat(lat1, lon1, 0)
var lon2 = wgs842bessel_lon(lat1, lon1, 0)

return bessel2rd_y(lat2, lon2)
}

function wgs842bessel_lat(lat1, lon1, h1)
{
var x1 = wgs84_x(lat1, lon1, h1)
var y1 = wgs84_y(lat1, lon1, h1)
var z1 = wgs84_z(lat1, lon1, h1)

var x2 = wgs842bessel_x(x1, y1, z1)
var y2 = wgs842bessel_y(x1, y1, z1)
var z2 = wgs842bessel_z(x1, y1, z1)

return bessel_lat(x2, y2, z2)
}

function wgs842bessel_lon(lat1, lon1, h1)
{
var x1 = wgs84_x(lat1, lon1, h1)
var y1 = wgs84_y(lat1, lon1, h1)
var z1 = wgs84_z(lat1, lon1, h1)

var x2 = wgs842bessel_x(x1, y1, z1)
var y2 = wgs842bessel_y(x1, y1, z1)
var z2 = wgs842bessel_z(x1, y1, z1)

return bessel_lon(x2, y2, z2)
}


function wgs842bessel_x(x1, y1, z1) {
var tx = -565.04
var ty = -49.91
var tz = -465.84
var ra = 0.0000019848
var rb = -0.0000017439
var rc = 0.0000090587
var sd = -0.0000040772

return x1 + tx + sd * x1 - rc * y1 + rb * z1
}

function wgs842bessel_y(x1, y1, z1) {
var tx = -565.04
var ty = -49.91
var tz = -465.84
var ra = 0.0000019848
var rb = -0.0000017439
var rc = 0.0000090587
var sd = -0.0000040772

return y1 + ty + rc * x1 + sd * y1 - ra * z1
}

function wgs842bessel_z(x1, y1, z1) {
var tx = -565.04
var ty = -49.91
var tz = -465.84
var ra = 0.0000019848
var rb = -0.0000017439
var rc = 0.0000090587
var sd = -0.0000040772

return z1 + tz - rb * x1 + ra * y1 + sd * z1
}

function wgs84_x(lat1, lon1, h1) {
var wgs84a = 6378137
var wgs84b = 6356752.314
var wgs84e2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84a * wgs84a)
var wgs84n = wgs84a / Math.sqrt(1 - wgs84e2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (wgs84n + h1) * Math.cos(rad(lat1)) * Math.cos(rad(lon1))
}


function wgs84_y(lat1, lon1, h1) {
var wgs84a = 6378137
var wgs84b = 6356752.314
var wgs84e2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84a * wgs84a)
var wgs84n = wgs84a / Math.sqrt(1 - wgs84e2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (wgs84n + h1) * Math.cos(rad(lat1)) * Math.sin(rad(lon1))
}

function wgs84_z(lat1, lon1, h1) {
var wgs84a = 6378137
var wgs84b = 6356752.314
var wgs84e2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84a * wgs84a)
var wgs84n = wgs84a / Math.sqrt(1 - wgs84e2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (wgs84n * (1 - wgs84e2) + h1) * Math.sin(rad(lat1))
}


function rad(x) { return (x * Math.PI) / 180 }



//---------------------------------------------------------------------



function bessel_x(lat1, lon1, h1)
{
var bessela = 6377397.155
var besselb = 6356078.963
var bessele2 = (bessela * bessela - besselb * besselb ) / (bessela * bessela)
var besseln = bessela / Math.sqrt(1 - bessele2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (besseln + h1) * Math.cos(rad(lat1)) * Math.cos(rad(lon1))
}

function bessel_y(lat1, lon1, h1)
{
var bessela = 6377397.155
var besselb = 6356078.963
var bessele2 = (bessela * bessela - besselb * besselb ) / (bessela * bessela)
var besseln = bessela / Math.sqrt(1 - bessele2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (besseln + h1) * Math.cos(rad(lat1)) * Math.sin(rad(lon1))
}


function bessel_z(lat1, lon1, h1) {
var bessela = 6377397.155
var besselb = 6356078.963
var bessele2 = (bessela * bessela - besselb * besselb ) / (bessela * bessela)
var besseln = bessela / Math.sqrt(1 - bessele2 * Math.pow(Math.sin(rad(lat1)),2))
if (eval(h1) == NaN) h1=0

return (besseln * (1 - bessele2) + h1) * Math.sin(rad(lat1))
}

function bessel_lat(x1, y1, z1) {
var bessela = 6377397.155
var besselb = 6356078.963
var bessele2 = (bessela * bessela - besselb * besselb) / (bessela * bessela)
var besseleps2 = (bessela * bessela - besselb * besselb) / (besselb * besselb)

var r1 = Math.sqrt(x1 * x1 + y1 * y1)
var theta1 = Math.atan((z1 * bessela) / (r1 * besselb))

var tanlat = (z1 + besseleps2 * besselb * Math.pow(Math.sin(theta1),3)) / (r1 - bessele2 * bessela * Math.pow(Math.cos(theta1),3))
return deg(Math.atan(tanlat))
}


function bessel_lon(x1, y1, z1) {
return deg(Math.atan(y1 / x1))
}


function bessel_h(x1, y1, z1) {
var bessela = 6377397.155
var besselb = 6356078.963
var bessele2 = (bessela * bessela - besselb * besselb) / (bessela * bessela)
var besseleps2 = (bessela * bessela - besselb * besselb) / (besselb * besselb)

var r1 = Math.sqrt(x1 * x1 + y1 * y1)
var theta1 = Math.atan((z1 * bessela) / (r1 * besselb))

var tanlat = (z1 + besseleps2 * besselb * Math.pow(Math.sin(theta1),3)) / (r1 - bessele2 * bessela * Math.pow(Math.cos(theta1),3))

var coslat = 1 / Math.sqrt(1 + tanlat * tanlat)
var Sinlat = tanlat / Math.sqrt(1 + tanlat * tanlat)

var besseln = bessela / Math.sqrt(1 - bessele2 * Sinlat * Sinlat)

return r1 / coslat - besseln
}




function wgs84_lat(x1, y1, z1) {
var wgs84a = 6378137
var wgs84b = 6356752.314
var wgs84e2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84a * wgs84a)
var wgs84eps2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84b * wgs84b)

var r1 = Math.sqrt(x1 * x1 + y1 * y1)
var theta1 = Math.atan((z1 * wgs84a) / (r1 * wgs84b))

var tanlat = (z1 + wgs84eps2 * wgs84b * Math.pow(Math.sin(theta1) ,3)) / (r1 - wgs84e2 * wgs84a * Math.pow(Math.cos(theta1),3))
return deg(Math.atan(tanlat))
}


function wgs84_lon(x1, y1, z1) {
return deg(Math.atan(y1 / x1))
}


function wgs84_h(x1, y1, z1)
{
var wgs84a = 6378137
var wgs84b = 6356752.314
var wgs84e2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84a * wgs84a)
var wgs84eps2 = (wgs84a * wgs84a - wgs84b * wgs84b) / (wgs84b * wgs84b)

var r1 = Math.sqrt(x1 * x1 + y1 * y1)
var theta1 = Math.atan((z1 * wgs84a) / (r1 * wgs84b))

var tanlat = (z1 + wgs84eps2 * wgs84b * Math.pow(Math.sin(theta1),3)) / (r1 - wgs84e2 * wgs84a * Math.pow(Math.cos(theta1),3))

var coslat = 1 / Math.sqrt(1 + tanlat * tanlat)
var Sinlat = tanlat / Math.sqrt(1 + tanlat * tanlat)

var wgs84n = wgs84a / Math.sqrt(1 - wgs84e2 * Sinlat * Sinlat)

return r1 / coslat - wgs84n
}


function bessel2wgs84_x(x1, y1, z1) {
var tx = 565.04
var ty = 49.91
var tz = 465.84
var ra = -0.0000019848
var rb = 0.0000017439
var rc = -0.0000090587
var sd = 0.0000040772

return x1 + tx + sd * x1 - rc * y1 + rb * z1
}

function bessel2wgs84_y(x1, y1, z1)
{
var tx = 565.04
var ty = 49.91
var tz = 465.84
var ra = -0.0000019848
var rb = 0.0000017439
var rc = -0.0000090587
var sd = 0.0000040772

return y1 + ty + rc * x1 + sd * y1 - ra * z1
}

function bessel2wgs84_z(x1, y1, z1)
{
var tx = 565.04
var ty = 49.91
var tz = 465.84
var ra = -0.0000019848
var rb = 0.0000017439
var rc = -0.0000090587
var sd = 0.0000040772

return z1 + tz - rb * x1 + ra * y1 + sd * z1
}


function bessel2wgs84_lat(lat1, lon1, h1)
{
var x1 = bessel_x(lat1, lon1, h1)
var y1 = bessel_y(lat1, lon1, h1)
var z1 = bessel_z(lat1, lon1, h1)

var x2 = bessel2wgs84_x(x1, y1, z1)
var y2 = bessel2wgs84_y(x1, y1, z1)
var z2 = bessel2wgs84_z(x1, y1, z1)

return wgs84_lat(x2, y2, z2)
}

function bessel2wgs84_lon(lat1, lon1, h1)
{
var x1 = bessel_x(lat1, lon1, h1)
var y1 = bessel_y(lat1, lon1, h1)
var z1 = bessel_z(lat1, lon1, h1)

var x2 = bessel2wgs84_x(x1, y1, z1)
var y2 = bessel2wgs84_y(x1, y1, z1)
var z2 = bessel2wgs84_z(x1, y1, z1)

return wgs84_lon(x2, y2, z2)
}

function bessel2wgs84_h(lat1, lon1, h1)
{
var x1 = bessel_x(lat1, lon1, h1)
var y1 = bessel_y(lat1, lon1, h1)
var z1 = bessel_z(lat1, lon1, h1)

var x2 = bessel2wgs84_x(x1, y1, z1)
var y2 = bessel2wgs84_y(x1, y1, z1)
var z2 = bessel2wgs84_z(x1, y1, z1)

return wgs84_h(x2, y2, z2)
}











function deg(x)
{ return (x / Math.PI) * 180 }


function modcrs(crs)
{
var twopi = 2 * Math.PI
return twopi - md(twopi - crs, twopi)
}

function modlon(Lon)
{
return md(Lon + Math.PI, 2 * Math.PI) - Math.PI
}

function md(Y ,X )
{
return Y - X * Math.floor(Y / X)
}


function atn2(Y, X)
{
var pi2 = Math.PI / 2
if (Math.abs(Y) >= Math.abs(X))
  { return Math.abs(Y)/Y * pi2 - Math.atan(X / Y) }
else
  {
  if (X > 0)
    { return Math.atan(Y / X) }
  else
   {
   if (Y >= 0)
      { return Math.PI + Math.atan(Y / X) }
    else
      { return -Math.PI + Math.atan(Y / X) }
    }
  }
}


function bessel2rd_x(lat1, lon1)
{
var dlat = (lat1 * 3600 - 187762.178) * 0.0001
var dlon = (lon1 * 3600 - 19395.5) * 0.0001

var c01 = 190066.98903
var c11 = -11830.85831
var c21 = -114.19754
var c03 = -32.3836
var c31 = -2.34078
var c13 = -0.60639
var c23 = 0.15774
var c41 = -0.04158
var c05 = -0.00661

var dx = c01 * dlon + c11 * dlat * dlon + c21 * dlat * dlat * dlon
dx = dx + c03 * Math.pow(dlon,3) + c31 * Math.pow(dlat,3) * dlon + c13 * dlat * Math.pow(dlon,3)
dx = dx + c23 * Math.pow(dlat,2) * Math.pow(dlon,3) + c41 * Math.pow(dlat,4) * dlon + c05 * Math.pow(dlon,5)

return 155000 + dx
}

function bessel2rd_y(lat1, lon1)
{
var dlat = (lat1 * 3600 - 187762.178) * 0.0001
var dlon = (lon1 * 3600 - 19395.5) * 0.0001

var d10 = 309020.3181
var d02 = 3638.36193
var d12 = -157.95222
var d20 = 72.97141
var d30 = 59.79734
var d22 = -6.43481
var d04 = 0.09351
var d32 = -0.07379
var d14 = -0.05419
var d40 = -0.03444

var dy = d10 * dlat + d02 * Math.pow(dlon,2) + d12 * dlat * Math.pow(dlon,2)
dy = dy + d20 * Math.pow(dlat,2) + d30 * Math.pow(dlat,3) + d22 * Math.pow(dlat,2) * Math.pow(dlon,2)
dy = dy + d04 * Math.pow(dlon,4) + d32 * Math.pow(dlat,3) * Math.pow(dlon,2) + d14 * dlat * Math.pow(dlon,4)
dy = dy + d40 * Math.pow(dlat,4)

return 463000 + dy
}




