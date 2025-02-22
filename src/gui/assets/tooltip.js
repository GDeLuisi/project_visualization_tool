window.dccFunctions = window.dccFunctions || {};
window.dccFunctions.timestampToUTC = function(value) {
     return new Date(value*1000).toLocaleString();
}