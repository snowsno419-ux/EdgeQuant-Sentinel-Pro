'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {generateKeyPairSync,sign}=require('node:crypto');
const S=require('../mobile-web/api/_lib/onboarding');
const TG=require('../mobile-web/api/_lib/telegram');
const {canonical,verifyObservation}=require('../mobile-web/api/_lib/core');
function req(method,body={},headers={}){return {method,body,headers:{origin:'https://edgequant-mobile-web.vercel.app',host:'edgequant-mobile-web.vercel.app','content-type':'application/json',...headers}}}
function res(){return {headers:{},statusCode:0,body:null,setHeader(k,v){this.headers[k]=v},status(n){this.statusCode=n;return this},json(x){this.body=x;return this}}}
function loadHandler(name,mockDb){const path=require.resolve('../mobile-web/api/_lib/db');const original=require(path),old=original.db;original.db=()=>mockDb;const routePath=['signup','resend-verification','verify-email','totp-setup','totp-confirm','channels','telegram-observation','telegram-inbox'].includes(name)?'../mobile-web/api/_lib/routes/'+name+'.js':'../mobile-web/api/'+name+'.js';const handlePath=require.resolve(routePath);delete require.cache[handlePath];const handler=require(handlePath);return {handler,reset(){original.db=old;delete require.cache[handlePath]}}}
test('signup validation strict input shape and role lock',()=>{
 assert.deepEqual(S.validateSignup({email:' A@EXAMPLE.COM ',password:'StrongPass1234',role:'receiver'}),{email:'a@example.com',password:'StrongPass1234',role:'receiver'});
 for(const bad of [{email:'a@example.com',password:'pass',role:'receiver'},{email:'a@example.com',password:'StrongPass1234',role:'admin'},{email:'a@example.com',password:'StrongPass1234',role:'receiver',mt5_password:'secret'},{email:'invalid',password:'StrongPass1234',role:'receiver'}])assert.equal(S.validateSignup(bad),null)
});
test('strong encrypted TOTP and authenticated corruption checks',()=>{
 const saved=process.env.EQ_TOTP_ENCRYPTION_KEY;process.env.EQ_TOTP_ENCRYPTION_KEY='a'.repeat(64);
 try{const secret=S.b32(Buffer.alloc(20,7));assert.match(secret,/^[A-Z2-7]+$/);const ciphertext=S.encryptTotp(secret);assert.notEqual(ciphertext,secret);assert.equal(S.decryptTotp(ciphertext),secret);assert.equal(S.decryptTotp(ciphertext.slice(0,-1)+'f'),null)}finally{if(saved===undefined)delete process.env.EQ_TOTP_ENCRYPTION_KEY;else process.env.EQ_TOTP_ENCRYPTION_KEY=saved}
});
test('registration cannot run without database, mail or encryption',async()=>{const previous=process.env.RESEND_API_KEY;delete process.env.RESEND_API_KEY;try{assert.equal(S.readyForRegistration(),false);const x=loadHandler('signup',null);try{const r=res();await x.handler(req('POST',{email:'demo@example.com',password:'StrongPass1234',role:'receiver'}),r);assert.equal(r.statusCode,503)}finally{x.reset()}}finally{if(previous!==undefined)process.env.RESEND_API_KEY=previous}});
test('TOTP confirmation rejects cross-origin POST',async()=>{const x=loadHandler('totp-confirm',{query:async()=>{throw Error('should not query')}});try{const r=res();await x.handler(req('POST',{}, {origin:'https://evil.test'}),r);assert.equal(r.statusCode,403)}finally{x.reset()}});
test('telegram source strict accepted allowlist and no secrets',()=>{
 const ok={chat_id:'-1001234567890123',kind:'LIMIT',label:'Gold Limit VIP',enabled:false};assert.deepEqual(TG.parseSource(ok),ok);
 for(const bad of [{...ok,enabled:'true'},{...ok,api_key:'secret'},{...ok,kind:'LIVE'},{...ok,chat_id:'group-private'},{...ok,label:'<script>'}])assert.equal(TG.parseSource(bad),null)
});
test('Telegram event exact structure; reply IDs maintained; ed25519 only',()=>{
 const {privateKey,publicKey}=generateKeyPairSync('ed25519');const p={worker_id:'telegram_worker_abc123',chat_id:'-1001234567890123',message_id:212,reply_to_id:211,kind:'new',edit_date_ms:0,event_id:'event_test_20261114_001',timestamp_ms:Date.now(),text:'cancel this entry ❌'};
 assert.equal(TG.validTelegramEvent(p),true);const sig=sign(null,Buffer.from(canonical(p)),privateKey).toString('base64'),pem=publicKey.export({type:'spki',format:'pem'});
 assert.equal(TG.verifyTelegram(p,sig,pem),true);assert.equal(TG.verifyTelegram({...p,reply_to_id:212},sig,pem),false);assert.equal(TG.validTelegramEvent({...p,mt5_password:'secret'}),false);assert.equal(TG.validTelegramEvent({...p,text:'a'.repeat(3001)}),false)
});
test('Telegram signed ingress cross-user channel authorization requires exact user key and enabled group',async()=>{
 const {privateKey,publicKey}=generateKeyPairSync('ed25519');const pem=publicKey.export({format:'pem',type:'spki'});
 const p={worker_id:'telegram_worker_abc123',chat_id:'-1001234567890123',message_id:22,reply_to_id:11,kind:'new',edit_date_ms:0,event_id:'event_test_20261114_002',timestamp_ms:Date.now(),text:'cancel this entry ❌'};
 const sig=sign(null,Buffer.from(canonical(p)),privateKey).toString('base64');
 const queries=[];const cx={query:async(sql,args)=>{queries.push({sql,args});if(sql.startsWith('SELECT k.public_key_pem'))return {rows:[{public_key_pem:pem,user_id:'owner-one',revoked_at:null}],rowCount:1};if(sql.startsWith('INSERT INTO telegram_event_ids'))return {rows:[{event_id:p.event_id}],rowCount:1};if(sql.startsWith('INSERT INTO telegram_inbox'))return {rows:[{message_id:22}],rowCount:1};return {rows:[],rowCount:1}},release(){}};
 const handler=loadHandler('telegram-observation',{connect:async()=>cx});try{const r=res();await handler.handler(req('POST',p,{'x-eq-signature':sig}),r);assert.equal(r.statusCode,202);const insert=queries.find(q=>q.sql.startsWith('INSERT INTO telegram_inbox'));assert.equal(insert.args[0],'owner-one');assert.equal(insert.args[3],11);assert.match(queries[0].sql,/d\.enabled=TRUE/);assert.match(queries[0].sql,/d\.user_id=k\.user_id/);assert.match(queries[0].sql,/r\.state='CONNECTED'/);assert.equal(r.body.executed,false)}finally{handler.reset()}
});
test('telegram ingestion rejects bad signatures before insert',async()=>{
 const {publicKey}=generateKeyPairSync('ed25519'),queries=[];const p={worker_id:'telegram_worker_abc123',chat_id:'-1001234567890123',message_id:22,reply_to_id:11,kind:'new',edit_date_ms:0,event_id:'event_test_20261114_003',timestamp_ms:Date.now(),text:'cancel this entry'};
 const cx={query:async(sql,args)=>{queries.push(sql);return {rows:[{public_key_pem:publicKey.export({format:'pem',type:'spki'}),user_id:'owner-one'}],rowCount:1}},release(){}};
 const handler=loadHandler('telegram-observation',{connect:async()=>cx});try{const r=res();await handler.handler(req('POST',p,{'x-eq-signature':'BAD'}),r);assert.equal(r.statusCode,401);assert.equal(queries.length,1)}finally{handler.reset()}
});
test('verified user channel GET scoped by user ID',async()=>{
 const m=require.resolve('../mobile-web/api/_lib/db');const orig=require(m),oldD=orig.db,oldS=orig.signedIn;const qs=[];orig.db=()=>({query:async(sql,args)=>{qs.push([sql,args]);return {rows:[]}}});orig.signedIn=async()=>({id:'owner-two'});
 const p=require.resolve('../mobile-web/api/_lib/routes/channels.js');delete require.cache[p];try{const r=res();await require(p)(req('GET'),r);assert.equal(r.statusCode,200);assert.deepEqual(qs[0][1],['owner-two']);assert.match(qs[0][0],/user_id=\$1/)}finally{orig.db=oldD;orig.signedIn=oldS;delete require.cache[p]}
});
