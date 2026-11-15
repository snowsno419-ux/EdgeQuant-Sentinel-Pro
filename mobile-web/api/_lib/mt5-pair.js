'use strict';
const {randomBytes,createPublicKey,verify,createHash}=require('node:crypto');
const {sha,answer}=require('./core');
const {db,signedIn}=require('./db');
const {sameOrigin}=require('./registry');
const {throttle}=require('./onboarding');
const ID=/^[a-zA-Z0-9_-]{12,80}$/;
const TOKEN=/^[a-zA-Z0-9_-]{43}$/;
const SERVER=/^[a-zA-Z0-9][a-zA-Z0-9 ._()/-]{2,99}$/;
function proofText(token,workerId,server,login){return ['EDGEQUANT-MT5-PAIR-V1',token,workerId,server,login].join('\n')}
function fingerprint(publicPem){return createHash('sha256').update(publicPem).digest('hex').slice(0,24)}
function validateClaim(b){
 if(!b||typeof b!=='object'||Array.isArray(b)||Object.keys(b).sort().join(',')!=='login_hint,public_key_pem,server,signature,token,worker_id')return null;
 if(!TOKEN.test(b.token)||!ID.test(b.worker_id)||typeof b.server!=='string'||!SERVER.test(b.server)||
    typeof b.login_hint!=='string'||!/^\d{4,18}$/.test(b.login_hint)||
    typeof b.public_key_pem!=='string'||b.public_key_pem.length>1000||
    typeof b.signature!=='string'||b.signature.length>180)return null;
 try{
  const key=createPublicKey(b.public_key_pem),sig=Buffer.from(b.signature,'base64');
  if(key.asymmetricKeyType!=='ed25519'||sig.length!==64||
    !verify(null,Buffer.from(proofText(b.token,b.worker_id,b.server,b.login_hint)),key,sig))return null;
  return {worker_id:b.worker_id,public_key_pem:key.export({format:'pem',type:'spki'}).toString(),server:b.server,login_hint:b.login_hint,token:b.token};
 }catch{return null}
}
module.exports=async function(req,res,action){
 if(!['start','status','claim','approve'].includes(action))return answer(res,404,{error:'unknown_pair_action'});
 if(req.method!==(action==='status'?'GET':'POST'))return answer(res,405,{error:'method_not_allowed'});
 if(action!=='status'&&action!=='claim'&&!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 if(action==='claim'){
  const p=validateClaim(req.body);if(!p)return answer(res,400,{error:'invalid_claim'});
  let cx;
  try{
   cx=await pool.connect();await cx.query('BEGIN');
   const q=await cx.query("SELECT p.broker_id,p.state,a.server,a.login_hint FROM mt5_worker_pairings p JOIN broker_accounts a ON a.id=p.broker_id WHERE p.token_digest=$1 AND p.expires_at>NOW() FOR UPDATE OF p",[sha(p.token)]);
   const item=q.rows[0];
   if(!item||item.state!=='PENDING'||item.server!==p.server||item.login_hint!==p.login_hint){await cx.query('ROLLBACK');return answer(res,409,{error:'expired_used_or_mismatched_pairing'})}
   await cx.query("UPDATE mt5_worker_pairings SET state='CLAIMED',claimed_worker_id=$2,claimed_public_key_pem=$3,claimed_at=NOW(),updated_at=NOW() WHERE broker_id=$1",[item.broker_id,p.worker_id,p.public_key_pem]);
   await cx.query('COMMIT');
   return answer(res,202,{claimed:true,awaiting_owner_approval:true,live_trade_execution:false});
  }catch{
   await cx?.query('ROLLBACK').catch(()=>{});
   return answer(res,503,{error:'pairing_claim_unavailable'});
  }finally{cx?.release()}
 }
 if(action==='status'){
  const brokerId=req.query?.broker_id;
  if(typeof brokerId!=='string'||!ID.test(brokerId))return answer(res,400,{error:'invalid_broker_id'});
  try{
   const user=await signedIn(req);if(!user)return answer(res,401,{error:'sign_in_required'});
   const pair=await pool.query("SELECT state,claimed_worker_id,claimed_public_key_pem,expires_at FROM mt5_worker_pairings WHERE broker_id=$1 AND user_id=$2",[brokerId,user.id]);
   const a=pair.rows[0];
   const k=await pool.query('SELECT id,revoked_at FROM worker_keys WHERE broker_id=$1 AND revoked_at IS NULL LIMIT 1',[brokerId]);
   return answer(res,200,{pairing:a?{state:new Date(a.expires_at)>new Date()?a.state:'EXPIRED',worker_id:a.claimed_worker_id||null,fingerprint:a.claimed_public_key_pem?fingerprint(a.claimed_public_key_pem):null,expires_at:a.expires_at}:null,worker_registered:k.rowCount>0,mt5_connected:false,live_trade_execution:false});
  }catch{return answer(res,503,{error:'pairing_status_unavailable'})}
 }
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const brokerId=req.body?.broker_id;
 if(!req.body||typeof req.body!=='object'||Array.isArray(req.body)||Object.keys(req.body).join(',')!=='broker_id'||typeof brokerId!=='string'||!ID.test(brokerId))return answer(res,400,{error:'invalid_broker_id'});
 try{
  const user=await signedIn(req);if(!user)return answer(res,401,{error:'sign_in_required'});
  const b=await pool.query('SELECT id,server,login_hint FROM broker_accounts WHERE id=$1 AND user_id=$2',[brokerId,user.id]);
  if(!b.rowCount)return answer(res,404,{error:'broker_not_found'});
  if(action==='start'){
   if(!await throttle(pool,'mt5-pair-start:'+user.id,10,3600))return answer(res,429,{error:'too_many_requests'});
   const token=randomBytes(32).toString('base64url');
   await pool.query("INSERT INTO mt5_worker_pairings(broker_id,user_id,token_digest,expires_at,state,claimed_worker_id,claimed_public_key_pem,claimed_at) VALUES($1,$2,$3,NOW()+INTERVAL '15 minutes','PENDING',NULL,NULL,NULL) ON CONFLICT(broker_id) DO UPDATE SET token_digest=EXCLUDED.token_digest,expires_at=EXCLUDED.expires_at,state='PENDING',claimed_worker_id=NULL,claimed_public_key_pem=NULL,claimed_at=NULL,updated_at=NOW()",[brokerId,user.id,sha(token)]);
   return answer(res,200,{broker_id:brokerId,pairing_token:token,expires_in_seconds:900,mode:'DEMO_READ_ONLY',live_trade_execution:false});
  }
  let cx;
  try{
   cx=await pool.connect();await cx.query('BEGIN');
   const p=await cx.query("SELECT state,claimed_worker_id,claimed_public_key_pem FROM mt5_worker_pairings WHERE broker_id=$1 AND user_id=$2 AND expires_at>NOW() FOR UPDATE",[brokerId,user.id]);
   const x=p.rows[0];
   if(!x||x.state!=='CLAIMED'||!x.claimed_worker_id||!x.claimed_public_key_pem){await cx.query('ROLLBACK');return answer(res,409,{error:'pairing_not_ready_for_approval'})}
   // Approving a replacement automatically revokes the prior read-only telemetry worker.
   await cx.query('UPDATE worker_keys SET revoked_at=NOW() WHERE broker_id=$1 AND revoked_at IS NULL',[brokerId]);
   await cx.query('INSERT INTO worker_keys(id,broker_id,public_key_pem) VALUES($1,$2,$3) ON CONFLICT(id) DO NOTHING',[x.claimed_worker_id,brokerId,x.claimed_public_key_pem]);
   const w=await cx.query('SELECT id,revoked_at FROM worker_keys WHERE id=$1 AND broker_id=$2 AND revoked_at IS NULL',[x.claimed_worker_id,brokerId]);
   if(!w.rowCount)throw Error('worker_id_collision');
   await cx.query("UPDATE mt5_worker_pairings SET state='APPROVED',updated_at=NOW() WHERE broker_id=$1",[brokerId]);
   await cx.query("UPDATE worker_provision_requests SET state='APPROVED',updated_at=NOW() WHERE broker_id=$1 AND user_id=$2 AND state IN ('PENDING','APPROVED','PROVISIONING')",[brokerId,user.id]);
   await cx.query('COMMIT');
   return answer(res,200,{approved:true,worker_id:x.claimed_worker_id,awaiting_signed_telemetry:true,live_trade_execution:false});
  }catch{await cx?.query('ROLLBACK').catch(()=>{});return answer(res,503,{error:'pairing_approval_unavailable'})}finally{cx?.release()}
 }catch{return answer(res,503,{error:'mt5_pairing_unavailable'})}
};

// Pure validation functions exposed for automated unit tests only; not HTTP routes.
module.exports._validation={proofText,validateClaim,fingerprint};
