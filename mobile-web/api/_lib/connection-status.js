'use strict';
// Pure, privacy-safe worker readiness summaries. No broker login or Telegram credentials.
const STALE_MS=10*60*1000;
function telegramConnection(request, enabledCount=0, now=Date.now()){
 const state=typeof request?.state==='string'?request.state:'NOT_REQUESTED';
 const seen=request?.last_seen_at?new Date(request.last_seen_at).getTime():NaN;
 const online=state==='CONNECTED'&&Number.isFinite(seen)&&seen<=now+30000&&seen>now-STALE_MS;
 const enabled=Math.max(0,Number.isFinite(Number(enabledCount))?Math.trunc(Number(enabledCount)):0);
 let next_step='REQUEST_PERSONAL_LISTENER';
 if(['PENDING','APPROVED','PROVISIONING'].includes(state))next_step='PROVISION_PRIVATE_TELEGRAM_WORKER';
 else if(state==='CONNECTED'&&!online)next_step='RECONNECT_TELEGRAM_WORKER';
 else if(online&&enabled===0)next_step='SELECT_TELEGRAM_CHANNEL';
 else if(online)next_step='MONITORING_READ_ONLY';
 else if(['CANCELLED','FAILED'].includes(state))next_step='REQUEST_PERSONAL_LISTENER';
 return {state,worker_online:online,selected_channel_count:enabled,monitoring:online&&enabled>0,
  next_step,last_seen_at:request?.last_seen_at||null,live_trade_execution:false};
}
function mt5Connection(brokers){
 const accounts=Array.isArray(brokers)?brokers:[];
 const active=accounts.filter(b=>b.status==='CONNECTED').length;
 return {registered_brokers:accounts.length,connected_demo_workers:active,worker_online:active>0,
  next_step:!accounts.length?'ADD_DEMO_BROKER':!active?'PAIR_OR_START_DEMO_WORKER':'MONITORING_READ_ONLY',
  live_trade_execution:false};
}
module.exports={telegramConnection,mt5Connection};
