'use strict';
// Owner-initiated read-only recovery planning, never trading. No storage or network.
(function(root,factory){const result=factory();if(typeof module==='object'&&module.exports)module.exports=result;if(root)root.EQRecoveryPreview=result;})(typeof window!=='undefined'?window:null,function(){
 function amount(x){if(x===null||x===undefined||x==='')return null;const n=Number(x);return Number.isFinite(n)?n:null}
 function preview(equity,reference,riskPct=0.25){
  const e=amount(equity),r=amount(reference),p=amount(riskPct);
  const missing={status:'UNAVAILABLE',recoveryNeeded:null,drawdownPct:null,riskBudget:null,orderExecution:false};
  if(e===null||r===null||p===null||e<=0||r<=0||p<=0||p>0.5)return missing;
  const needed=Math.max(0,r-e),drawdown=needed/r*100;
  return {status:drawdown>=3?'SIMULATED_RECOVERY':'STANDBY',recoveryNeeded:needed,
    drawdownPct:drawdown,riskBudget:drawdown>=3?e*p/100:null,orderExecution:false,
    layers:'Risk limit applies across the entire Telegram signal, not per layer.'};
 }
 return Object.freeze({preview});
});
