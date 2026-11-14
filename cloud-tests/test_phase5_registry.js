'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {randomBytes}=require('node:crypto');
const R=require('../mobile-web/api/_lib/registry');
function req(method,body={},headers={}){return {method,body,headers:{origin:'https://edgequant-mobile-web.vercel.app',host:'edgequant-mobile-web.vercel.app','content-type':'application/json',...headers}}}
function res(){const r={headers:{},statusCode:0,body:null,setHeader(k,v){r.headers[k]=v},status(n){r.statusCode=n;return r},json(v){r.body=v;return r}};return r}
function handlerWithMock(file,mockDb,mockSignIn){
  const path=require.resolve('../mobile-web/api/_lib/db');
  const mod=require(path),previousDb=mod.db,previousSigned=mod.signedIn;
  mod.db=()=>mockDb;mod.signedIn=async()=>mockSignIn;
  const handlerPath=require.resolve('../mobile-web/api/'+file);
  delete require.cache[handlerPath];const fn=require(handlerPath);
  return {fn,reset(){mod.db=previousDb;mod.signedIn=previousSigned;delete require.cache[handlerPath]}}
}
test('registry validates DEMO metadata only and rejects secrets/REAL/malformed server',()=>{
  const good={label:'Gold DEMO',broker:'IC Markets',server:'ICMarketsSC-Demo',login:'52985798',mode:'DEMO'};
  assert.deepEqual(R.parseBrokerMetadata(good),{label:good.label,broker:good.broker,server:good.server,login:good.login});
  for(const extra of [{password:'123'}, {terminal:'C:/MT5'},{api_key:'secret'}])assert.equal(R.parseBrokerMetadata({...good,...extra}),null);
  assert.equal(R.parseBrokerMetadata({...good,mode:'REAL'}),null);
  assert.equal(R.parseBrokerMetadata({...good,server:'<script>alert(1)</script>'}),null);
  assert.equal(R.parseBrokerMetadata({...good,login:'abcdef'}),null);
  assert.equal(R.parseBrokerMetadata({...good,login:52985798}),null);
});
test('same-origin guard requires HTTPS and rejects cross-origin',()=>{
  assert.equal(R.sameOrigin(req('POST')),true);
  assert.equal(R.sameOrigin(req('POST',{}, {origin:'https://evil.example'})),false);
  assert.equal(R.sameOrigin(req('POST',{}, {origin:'http://edgequant-mobile-web.vercel.app'})),false);
  assert.equal(R.sameOrigin(req('POST',{}, {origin:'https://edgequant-mobile-web.vercel.app.evil.test'})),false);
});
test('snapshot freshness fails closed',()=>{
  assert.equal(R.snapshotStatus(null,true,1000000),'OFFLINE');
  assert.equal(R.snapshotStatus(990000,true,1000000),'CONNECTED');
  assert.equal(R.snapshotStatus(800000,true,1000000),'STALE');
  assert.equal(R.snapshotStatus(990000,false,1000000),'STALE');
});
test('POST broker requires verified session',async()=>{
  const m=handlerWithMock('brokers.js',{query:async()=>{throw Error('should not query')}},null);
  try{const r=res();await m.fn(req('POST',{label:'Gold DEMO'}),r);assert.equal(r.statusCode,401)}finally{m.reset()}
});
test('GET broker registry scoped strictly to the authenticated user id',async()=>{
  const queries=[];const pool={query:async(sql,args)=>{queries.push({sql,args});return {rows:[{id:'abc123456789',label:'IC',broker:'IC Markets',server:'ICMarketsSC-Demo',masked_login:'5798',created_at:'2026-11-14T00:00:00Z'}]}}};
  const m=handlerWithMock('brokers.js',pool,{id:'client-user-123',email:'demo@example.test',role:'receiver'});
  try{const r=res();await m.fn(req('GET'),r);assert.equal(r.statusCode,200);assert.equal(queries.length,1);assert.match(queries[0].sql,/WHERE user_id=\$1/);assert.equal(queries[0].args[0],'client-user-123');assert.equal(r.body.brokers[0].login_hint,'••••5798');assert.equal(JSON.stringify(r.body).includes('52985798'),false)}finally{m.reset()}
});
test('POST registers DEMO broker without trading action, in isolated transaction',async()=>{
  const queries=[];let released=0;
  const cx={query:async(sql,args)=>{queries.push({sql,args});if(sql.startsWith('SELECT count(*)'))return {rows:[{n:1}]};return {rows:[],rowCount:1}},release:()=>released++};
  const pool={connect:async()=>cx};const m=handlerWithMock('brokers.js',pool,{id:'client-user-123',role:'receiver'});
  try{const r=res();await m.fn(req('POST',{label:'My Gold DEMO',broker:'IC Markets',server:'ICMarketsSC-Demo',login:'52985798',mode:'DEMO'}),r);assert.equal(r.statusCode,201);assert.equal(r.body.status,'OFFLINE');assert.equal(r.body.worker_provisioned,false);assert.equal(r.body.live_trade_execution,false);const insert=queries.find(x=>x.sql.startsWith('INSERT INTO broker_accounts'));assert.equal(insert.args[1],'client-user-123');assert.equal(insert.args[5],'52985798');assert.equal(r.body.login_hint,'••••5798');assert.equal(released,1);assert.ok(queries.some(x=>x.sql==='COMMIT'))}finally{m.reset()}
});
test('POST broker limit blocks account creation',async()=>{
  const queries=[];const cx={query:async(sql,args)=>{queries.push(sql);if(sql.startsWith('SELECT count(*)'))return {rows:[{n:10}]};return {rows:[]}},release:()=>{}};
  const m=handlerWithMock('brokers.js',{connect:async()=>cx},{id:'client-user-123'});
  try{const r=res();await m.fn(req('POST',{label:'Gold DEMO',broker:'IC Markets',server:'ICMarketsSC-Demo',login:'52985798',mode:'DEMO'}),r);assert.equal(r.statusCode,409);assert.equal(r.body.error,'broker_limit_reached');assert.ok(!queries.some(x=>x.startsWith('INSERT INTO')))}finally{m.reset()}
});
test('cross-origin request rejected before broker write',async()=>{
  const m=handlerWithMock('brokers.js',{connect:async()=>{throw Error('must not connect')}},{id:'client-user-123'});
  try{const r=res();await m.fn(req('POST',{}, {origin:'https://evil.test'}),r);assert.equal(r.statusCode,403)}finally{m.reset()}
});
test('logout revokes session digest only, expires cookie',async()=>{
  let sqlArgs=[];const m=handlerWithMock('logout.js',{query:async(sql,args)=>{sqlArgs=[sql,args]}},null);
  try{const token=randomBytes(40).toString('base64url');const r=res();await m.fn(req('POST',{}, {cookie:'__Host-eq_session='+token}),r);assert.equal(r.statusCode,200);assert.match(sqlArgs[0],/DELETE FROM sessions WHERE token_digest=\$1/);assert.equal(sqlArgs[1][0].length,64);assert.equal(String(r.headers['Set-Cookie']).includes('Max-Age=0'),true)}finally{m.reset()}
});
test('logout rejects cross-site requests',async()=>{
  const m=handlerWithMock('logout.js',{query:async()=>{throw Error('must not delete')}},null);
  try{const r=res();await m.fn(req('POST',{}, {origin:'https://evil.test'}),r);assert.equal(r.statusCode,403)}finally{m.reset()}
});
test('no database -> registry and logout fail closed',async()=>{
  const a=await Promise.all(['brokers.js','logout.js'].map(async f=>{const m=handlerWithMock(f,null,null);try{const r=res();await m.fn(req('POST'),r);return r.statusCode}finally{m.reset()}}));assert.deepEqual(a,[503,503])
});
