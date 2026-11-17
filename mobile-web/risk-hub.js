'use strict';
// EdgeQuant Option B: source-neutral broker risk math for READ-ONLY web previews.
// A broker's daily net must come from signed MT5 deal history, NOT just floating P&L.
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.EdgeQuantRiskHub=api;
})(typeof window!=='undefined'?window:null,function(){
 function finite(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null}
 function bounded(n){return Math.min(100,Math.max(0,n))}
 function calculate(account={},policy={}){
  const cap=finite(policy.lossLimit),target=finite(policy.targetLimit);
  const today=finite(account.today_trading_net),floating=finite(account.floating);
  const enabled=policy.lossEnabled===true&&cap!==null&&cap>0;
  const targetEnabled=policy.targetEnabled===true&&target!==null&&target>0;
  const known=account.status==='CONNECTED'&&today!==null&&floating!==null;
  const effective=known?today+floating:null;
  const lossUsed=known?Math.max(0,-effective):null;
  const lossPercent=enabled&&known?bounded(lossUsed/cap*100):null;
  const targetPercent=targetEnabled&&known?bounded(Math.max(0,today)/target*100):null;
  return {
   connected:account.status==='CONNECTED',dataReady:known,
   dailyNet:today,floating:account.status==='CONNECTED'?floating:null,
   lossEnabled:enabled,targetEnabled,
   lossUsed:enabled?lossUsed:null,lossPercent,targetPercent,
   remaining:enabled&&known?Math.max(0,cap-lossUsed):null,
   lossHit:Boolean(enabled&&known&&lossUsed>=cap),
   targetHit:Boolean(targetEnabled&&known&&today>=target),
   floatingExposurePercent:account.status==='CONNECTED'&&floating!==null&&enabled?
      bounded(Math.max(0,-floating)/cap*100):null,
   status:!enabled?'OFF':!known?'UNAVAILABLE':lossUsed>=cap?'BREACHED':
       lossPercent>=85?'DANGER':lossPercent>=65?'CAUTION':'SAFE',
   enforcement:'NOT_CONNECTED_WEB_READ_ONLY'
  };
 }
 return Object.freeze({finite,calculate});
});
