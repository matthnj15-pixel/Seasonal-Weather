// Exercise the exact date-resolver source used by the iPhone script.
const fs=require("fs");
const vm=require("vm");
const assert=require("assert");
const original=fs.readFileSync("Seasonal_Hourly_Weather.js","utf8");
const first=original.indexOf("// SPECIAL EDITIONS:");
const last=original.indexOf("// GPS LOCATION.",first);
if(first<0 || last<0)throw Error("Missing holiday resolver");
const source=original.slice(first,last);
const settings={
  specialEditions:true,
  specialDates:[
    {key:"birthday_a",month:10,day:6,label:"Birthday"},
    {key:"birthday_b",month:7,day:9,label:"Birthday"}
  ],
  testEdition:null
};
const context={SETTINGS:settings,config:{runsInWidget:true},Date,Math};
const dates=vm.runInNewContext(source+";({resolveSpecialEdition,easterSunday,nthWeekday,lastWeekday})",context);
function check(month,day,expected,year=2026,offset=0) {
  const time=Date.UTC(year,month-1,day,12);
  const answer=dates.resolveSpecialEdition(null,{utc_offset_seconds:offset},time);
  assert.strictEqual(answer,expected,year+"-"+month+"-"+day+" expected "+expected+" got "+answer);
}
check(7,4,"july4");
check(12,25,"christmas");
check(12,31,"newyear");
check(1,1,"newyear");
check(4,5,"easter");
check(11,26,"thanksgiving");
check(10,31,"halloween");
check(5,25,"memorial");
check(9,7,"labor");
check(10,6,"birthday_a");
check(7,9,"birthday_b");
check(10,28,null);
check(3,28,"easter",2027);
check(11,25,"thanksgiving",2027);
check(5,31,"memorial",2027);
check(9,6,"labor",2027);
assert.strictEqual(JSON.stringify(dates.easterSunday(2026)),JSON.stringify({month:4,day:5}));
const nearMidnight=Date.UTC(2026,6,5,2,30);
assert.strictEqual(dates.resolveSpecialEdition(null,{utc_offset_seconds:-4*3600},nearMidnight),"july4");
const notHoliday=Date.UTC(2026,6,5,14);
assert.strictEqual(dates.resolveSpecialEdition(null,{utc_offset_seconds:0},notHoliday),null);
settings.specialEditions=false;
check(12,25,null);
settings.specialEditions=true;
context.config.runsInWidget=false;
settings.testEdition="halloween";
check(10,28,"halloween");
settings.testEdition=null;
check(10,28,null);
console.log("Holiday dates: 2026/2027, birthdays, New Year's Eve, local time, preview and opt-out passed.");
