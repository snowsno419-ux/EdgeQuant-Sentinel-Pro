'use strict';
// Pure validation helpers for EdgeQuant read-only DEMO broker metadata.
// Never accept a terminal path, account password, API token, or a live trading mode.
function humanText(value,min,max){
  if(typeof value!=='string'||value.length>max)return null;
  const v=value.trim().replace(/\s+/g,' ');
  if(v.length<min||v.length>max||/[\u0000-\u001f\u007f<>]/u.test(v))return null;
  return v;
}
function parseBrokerMetadata(body){
  if(!body||typeof body!=='object'||Array.isArray(body))return null;
  const allowed=['broker','label','login','mode','server'];
  if(Object.keys(body).sort().join(',')!==allowed.join(','))return null;
  const label=humanText(body.label,2,64),broker=humanText(body.broker,2,64),server=humanText(body.server,3,100);
  const login=body.login;
  if(!label||!broker||!server||typeof login!=='string'||!/^\d{4,18}$/.test(login)||body.mode!=='DEMO')return null;
  if(!/^[A-Za-z0-9][A-Za-z0-9 ._()\/-]{2,99}$/.test(server))return null;
  return {label,broker,server,login};
}
function sameOrigin(req){
  try{
    const origin=req?.headers?.origin,host=req?.headers?.host;
    if(typeof origin!=='string'||typeof host!=='string'||!host||origin.length>255)return false;
    const u=new URL(origin);
    return u.protocol==='https:'&&u.host===host&&u.pathname==='/'&&u.search===''&&u.hash==='';
  }catch{return false}
}
function snapshotStatus(observedAt,connected,now=Date.now()){
  if(observedAt===null||observedAt===undefined)return 'OFFLINE';
  const t=Number(observedAt);
  return Number.isFinite(t)&&t<=now+30000&&t>now-120000&&connected===true?'CONNECTED':'STALE';
}
module.exports={parseBrokerMetadata,sameOrigin,snapshotStatus};
