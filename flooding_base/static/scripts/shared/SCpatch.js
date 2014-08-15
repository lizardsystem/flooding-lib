//----------------------------------------------------------------------------
// Isomorphic SmartClient 6.5.1 patch
// Purpose: Fix for problem in LGPL version only - JS crash when we receive 
// an HTTP error back from the server 
// 
// Applies to SmartClient 6.5.1 LGPL build only
//----------------------------------------------------------------------------

if (window.isc && isc.version.startsWith("6.5.1/") ){
if (isc.RestDataSource) {
isc.RestDataSource.addMethods({
transformResponse:function(_1,_2,_3) {
if(_1.status<0)return _1;
if(this.dataFormat=="json"){
var _4=_3.response||{};
_1.status=this.getValidStatus(_4.status);
if(_1.status==isc.DSResponse.STATUS_VALIDATION_ERROR){
var _5=_4.errors;
if(isc.isAn.Array(_5)){
if(_5.length>1){
this.logWarn("server returned an array of errors - ignoring all but the first one")
}
_5=_5[0]
}
_1.errors=_5
}else if(_1.status<0){
_1.data=_4.data
}
if(_4.totalRows!=null)_1.totalRows=_4.totalRows;
if(_4.startRow!=null)_1.startRow=_4.startRow;
if(_4.endRow!=null)_1.endRow=_4.endRow
}else{
_1.status=this.getValidStatus(_3.selectString("//status"));
if(_1.status==isc.DSResponse.STATUS_VALIDATION_ERROR){
var _5=_3.selectNodes("//errors");
_5=isc.xml.toJS(_5);
if(_5.length>1){this.logWarn("server returned an array of errors - ignoring all but the first one")
}
_5=_5[0];
_1.errors=_5
}else if(
_1.status<0){
_1.data=_3.selectString("//data")
}
var _6=_3.selectNumber("//totalRows");
if(_6!=null)_1.totalRows=_6;
var _7=_3.selectNumber("//startRow");
if(_7!=null)_1.startRow=_7;
var _8=_3.selectNumber("//endRow");
if(_8!=null)_1.endRow=_8
}
return _1
}
});
}

if (isc.WSDataSource) {
isc.WSDataSource.addMethods({
transformResponse:function(_1,_2,_3) {
if(!_3 || !_3.selectString)return;
_1.status=_3.selectString("//status");
if(isc.isA.String(_1.status)){
var _4=isc.DSResponse[_1.status];
if(_1.status==null){
this.logWarn("Unable to map response code: "+_4+" to a DSResponse code, setting status to DSResponse.STATUS_FAILURE.");
_4=isc.DSResponse.STATUS_FAILURE
}else{
_1.status=_4
}
}
if(_1.status==isc.DSResponse.STATUS_VALIDATION_ERROR){
var _5=_3.selectNodes("//errors/*");
_1.errors=isc.xml.toJS(_5,null,this)
}
_1.totalRows=_3.selectNumber("//totalRows");
_1.startRow=_3.selectNumber("//startRow");
_1.endRow=_3.selectNumber("//endRow")
}
});
}

if (isc.RPCManager) {
isc.RPCManager.addClassMethods({
performTransactionReply:function(_1,_2,_3){
var _4=this.getTransaction(_1);
if(!_4){
this.logWarn("No such transaction "+_1);
return false
}
_4.receiveTime=isc.timeStamp();
_4.changed();
isc.RPCManager.$410.remove(_1);
this.logInfo("transaction "+_1+" arrived after "+(_4.receiveTime-_4.sendTime)+"ms");
if(_2==null){
this.logFatal("No results for transaction "+_1);
return false
}
if(_4.transport=="xmlHttpRequest"){
var _5=_2;
_4.xmlHttpRequest=_5;
_2=_5.responseText;
var _6;
try{
_6=_5.status
}catch(e){
this.logWarn("Unable to access XHR.status - network cable unplugged?");
_6=-1
}
if(_6==1223)_6=204;
if(_6==0&&(location.protocol=="file:"||location.protocol=="app-resource:"))_6=200;
_4.httpResponseCode=_6;
_4.httpResponseText=_5.responseText;
if(_6!=-1&&!_4.ignoreReloginMarkers&&this.processLoginStatusText(_5,_1)){
return
}
if(_6!=-1&&this.responseRequiresLogin(_5,_1)){
this.handleLoginRequired(_1);
return
}
if(_6!=-1&&this.responseIsRelogin(_5,_1)){
this.handleLoginRequired(_1);
return
}
if(_6>299||_6<200){
var _7=_4.URL;
if(_4.isProxied){
_7=_4.proxiedURL+" (via proxy: "+_7+")"
}
_2=this.$39c(_4,{
data:"Transport error - HTTP code: "+_6+" for URL: "+_7+(_6==302?" This error is likely the result"+" of a redirect to a server other than the origin"+" server or a redirect loop.":""),
status:isc.RPCResponse.STATUS_TRANSPORT_ERROR
});
this.logDebug("RPC request to: "+_7+" returned with http response code: "+_6+". Response text:\n"+_5.responseText)
_4.status=isc.RPCResponse.STATUS_TRANSPORT_ERROR;
}
}
_4.results=_2;
this.$39d(_1);
return true
},
createRPCResponse:function(_1,_2,_3){
return isc.addProperties({
operationId:_2.operation.ID,
clientContext:_2.clientContext,
context:_2,
transactionNum:_1.transactionNum,
httpResponseCode:_1.httpResponseCode,
httpResponseText:_1.httpResponseText,
xmlHttpRequest:_1.xmlHttpRequest,
transport:_1.transport,
status:_1.status,
clientOnly:_2.clientOnly
},_3)}
});
}
} else if (window.isc) {
isc.Log.logWarn("Patch for SmartClient 6.5.1 build included in this application. " +
            "You are currently running SmartClient version '"+ isc.version + 
            "'. This patch is not compatible with this build and will have no effect. " +
            "It should be removed from your application source.");
}

// End of patch
// ------------
