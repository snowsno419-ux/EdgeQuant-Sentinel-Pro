'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {canonical}=require('../mobile-web/api/_lib/core');
const v=require('../mobile-web/api/_lib/routes/telegram-personal-sync')._validation;
function payload(){
 return {worker_id:'worker_1234567890',event_id:'event_1234567890',timestamp_ms:Date.now(),dialogs:[
  {chat_id:'-1001234567890',dialog_type:'channel',label:'Gold Limit VIP'},
  {chat_id:'-1001234567891',dialog_type:'supergroup',label:'Friends Forex'}
 ]};
}
test('personal cloud sync checks exact schema, clock skew and no credentials',()=>{
 const b=payload();
 assert.equal(v.validBody(b),true);
 assert.equal(v.validBody({...b,phone:'+12345'}),false);
 assert.equal(v.validBody({...b,otp:'123456'}),false);
 assert.equal(v.validBody({...b,dialogs:[...b.dialogs,b.dialogs[0]]}),false);
 assert.equal(v.validBody({...b,timestamp_ms:Date.now()-120000}),false);
 assert.equal(v.validBody({...b,dialogs:[{chat_id:'1',dialog_type:'channel',label:'Invalid'}]}),false);
 assert.equal(v.validBody({...b,dialogs:[{chat_id:'-1001234567890',dialog_type:'private',label:'Wrong type'}]}),false);
 assert.equal(v.validBody({...b,dialogs:[{chat_id:'-1001234567890',dialog_type:'channel',label:'<img>'}]}),false);
});
test('signed sync requires matching Ed25519 worker key and immutable canonical body',()=>{
 const {privateKey,publicKey}=crypto.generateKeyPairSync('ed25519'),body=payload();
 const pem=publicKey.export({type:'spki',format:'pem'}).toString();
 const signature=crypto.sign(null,Buffer.from(canonical(body)),privateKey).toString('base64');
 assert.equal(v.verifyWorker(body,signature,pem),true);
 assert.equal(v.verifyWorker({...body,timestamp_ms:body.timestamp_ms+1},signature,pem),false);
 assert.equal(v.verifyWorker(body,'junk',pem),false);
 const different=crypto.generateKeyPairSync('ed25519').publicKey.export({type:'spki',format:'pem'}).toString();
 assert.equal(v.verifyWorker(body,signature,different),false);
});
