'use strict';
// Signed, worker-only dialog metadata sync. Never accepts phone, OTP, 2FA or sessions.
const {answer,canonical}=require('../core');
const {db}=require('../db');
const {createPublicKey,verify}=require('node:crypto');
const ID=/^[A-Za-z0-9_-]{12,80}$/;
const CHAT=/^-?[0-9]{5,20}$/;
function validBody(b){
 if(!b||typeof b!=='object'||Array.isArray(b)||Object.keys(b).sort().join(',')!=='dialogs,event_id,timestamp_ms,worker_id')return false;
 if(!ID.test(b.worker_id)||!ID.test(b.event_id)||!Number.isSafeInteger(b.timestamp_ms)||Math.abs(Date.now()-b.timestamp_ms)>90000||!Array.isArray(b.dialogs)||b.dialogs.length>100)return false;
 const ids=new Set();
 return b.dialogs.every(d=>{
  if(!d||typeof d!=='object'||Array.isArray(d)||Object.keys(d).sort().join(',')!=='chat_id,dialog_type,label')return false;
  if(typeof d.chat_id!=='string'||!CHAT.test(d.chat_id)||ids.has(d.chat_id)||typeof d.label!=='string'||d.label.trim().length<1||d.label.length>100||/[\u0000-\u001f\u007f<>]/u.test(d.label)||!['channel','group','supergroup'].includes(d.dialog_type))return false;
  ids.add(d.chat_id);return true;
 });
}
function verifyWorker(body,signature,pem){
 try{
  if(typeof signature!=='string'||signature.length>180)return false;
  const key=createPublicKey(pem),raw=Buffer.from(signature,'base64');
  return key.asymmetricKeyType==='ed25519'&&raw.length===64&&verify(null,Buffer.from(canonical(body),'utf8'),key,raw);
 }catch{return false}
}
module.exports=async(req,res)=>{
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 const b=req.body;if(!validBody(b))return answer(res,400,{error:'invalid_personal_dialog_sync'});
 const signature=req.headers['x-eq-signature'];
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 let cx;
 try{
  cx=await pool.connect();await cx.query('BEGIN');
  const k=await cx.query("SELECT k.public_key_pem,k.user_id FROM telegram_listener_keys k JOIN telegram_listener_requests r ON r.user_id=k.user_id WHERE k.id=$1 AND k.revoked_at IS NULL AND r.mode='personal' AND r.state IN ('APPROVED','PROVISIONING','CONNECTED') FOR UPDATE OF r",[b.worker_id]);
  const worker=k.rows[0];
  if(!worker||!verifyWorker(b,signature,worker.public_key_pem)){await cx.query('ROLLBACK');return answer(res,401,{error:'unauthorized_personal_worker'})}
  const e=await cx.query('INSERT INTO telegram_event_ids(worker_id,event_id) VALUES($1,$2) ON CONFLICT DO NOTHING RETURNING event_id',[b.worker_id,b.event_id]);
  if(!e.rowCount){await cx.query('ROLLBACK');return answer(res,409,{error:'replayed_personal_sync'})}
  for(const d of b.dialogs){
   await cx.query("INSERT INTO telegram_personal_dialogs(user_id,chat_id,label,dialog_type,enabled,last_discovered_at) VALUES($1,$2,$3,$4,FALSE,NOW()) ON CONFLICT(user_id,chat_id) DO UPDATE SET label=EXCLUDED.label,dialog_type=EXCLUDED.dialog_type,last_discovered_at=NOW()",[worker.user_id,d.chat_id,d.label.trim(),d.dialog_type]);
  }
  await cx.query("UPDATE telegram_listener_requests SET state='CONNECTED',last_seen_at=NOW(),updated_at=NOW() WHERE user_id=$1",[worker.user_id]);
  const selected=await cx.query("SELECT chat_id FROM telegram_personal_dialogs WHERE user_id=$1 AND enabled=TRUE AND last_discovered_at>NOW()-INTERVAL '10 minutes' LIMIT 200",[worker.user_id]);
  await cx.query('COMMIT');
  return answer(res,202,{synced:b.dialogs.length,enabled_chat_ids:selected.rows.map(x=>x.chat_id),read_only:true,live_trade_execution:false});
 }catch{
  if(cx)await cx.query('ROLLBACK').catch(()=>{});
  return answer(res,503,{error:'personal_sync_unavailable'});
 }finally{cx?.release()}
};
module.exports._validation={validBody,verifyWorker};
