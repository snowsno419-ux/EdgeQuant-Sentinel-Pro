'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const S=require('../mobile-web/api/_lib/connection-status');
function request(){return {state:'CONNECTED',last_seen_at:new Date('2026-11-17T00:00:00Z').toISOString()}}
test('personal Telegram status requires a fresh connected signed worker',()=>{
 const now=Date.parse('2026-11-17T00:04:00Z');
 const online=S.telegramConnection(request(),2,now);
 assert.equal(online.worker_online,true);assert.equal(online.monitoring,true);
 assert.equal(online.selected_channel_count,2);assert.equal(online.live_trade_execution,false);
 const offline=S.telegramConnection(request(),2,now+11*60*1000);
 assert.equal(offline.worker_online,false);assert.equal(offline.monitoring,false);
 assert.equal(offline.next_step,'RECONNECT_TELEGRAM_WORKER');
});
test('pending request, selected channels and false online claims are distinguished',()=>{
 const now=Date.parse('2026-11-17T00:04:00Z');
 assert.equal(S.telegramConnection(null,0,now).next_step,'REQUEST_PERSONAL_LISTENER');
 assert.equal(S.telegramConnection({state:'PENDING',last_seen_at:new Date(now).toISOString()},1,now).worker_online,false);
 assert.equal(S.telegramConnection(request(),0,now).next_step,'SELECT_TELEGRAM_CHANNEL');
 assert.equal(S.telegramConnection({state:'CONNECTED',last_seen_at:'invalid-date'},1,now).worker_online,false);
 assert.equal(S.telegramConnection({state:'CONNECTED',last_seen_at:new Date(now+60*1000).toISOString()},1,now).worker_online,false);
});
test('DEMO worker readiness counts only fresh signed CONNECTED accounts',()=>{
 assert.equal(S.mt5Connection([]).next_step,'ADD_DEMO_BROKER');
 const b=S.mt5Connection([{status:'STALE'},{status:'CONNECTED'},{status:'OFFLINE'}]);
 assert.equal(b.registered_brokers,3);assert.equal(b.connected_demo_workers,1);
 assert.equal(b.worker_online,true);assert.equal(b.live_trade_execution,false);
});
test('dashboard uses authenticated per-user Telegram & DEMO worker data and masks MT5 login',async()=>{
 const dbPath=require.resolve('../mobile-web/api/_lib/db');
 const mod=require(dbPath),oldDB=mod.db,oldAuth=mod.signedIn;
 const queryLog=[];
 mod.db=()=>({query:async(sql,args)=>{queryLog.push({sql,args});if(sql.includes('FROM broker_accounts a'))return {rows:[{id:'broker_1234567890',label:'My DEMO',broker:'IC',server:'ICMarketsSC-Demo',login_hint:'52985798',observed_at:Date.now()-30000,balance:'200.00',equity:'210.00',floating:'10.00',open_positions:1,pending_orders:2,terminal_connected:true}]}; if(sql.includes('FROM telegram_listener_requests r'))return {rows:[{state:'PENDING',last_seen_at:null,enabled_count:'0'}]};throw Error('unexpected query')}});
 mod.signedIn=async()=>({id:'owner-abc',role:'receiver'});
 const route=require.resolve('../mobile-web/api/dashboard.js');delete require.cache[route];
 const res={setHeader(){},status(n){this.statusCode=n;return this},json(b){this.body=b;return this}};
 try{
  await require(route)({method:'GET',headers:{}},res);
  assert.equal(res.statusCode,200);assert.equal(res.body.connections.telegram.state,'PENDING');
  assert.equal(res.body.connections.telegram.worker_online,false);assert.equal(res.body.connections.mt5.worker_online,true);
  assert.equal(res.body.live_trade_execution,false);
  assert.equal(res.body.brokers[0].login_hint.includes('52985798'),false);
  assert.equal(queryLog.length,2);
  assert.ok(queryLog.every(q=>q.args?.length===1&&q.args[0]==='owner-abc'));
  assert.match(queryLog[0].sql,/a.user_id=\$1/);
  assert.match(queryLog[1].sql,/r.user_id=\$1/);
 }finally{mod.db=oldDB;mod.signedIn=oldAuth;delete require.cache[route]}
});
