'use strict';
// Explicit owner disconnect: disables personal sources and revokes signed worker access.
const {answer}=require('../core');
const {db,signedIn}=require('../db');
const {sameOrigin}=require('../registry');
module.exports=async(req,res)=>{
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 if(!req.body||typeof req.body!=='object'||Array.isArray(req.body)||Object.keys(req.body).length)return answer(res,400,{error:'invalid_request'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 let cx;
 try{
  const user=await signedIn(req);if(!user)return answer(res,401,{error:'sign_in_required'});
  cx=await pool.connect();await cx.query('BEGIN');
  await cx.query("UPDATE telegram_listener_requests SET state='CANCELLED',last_seen_at=NULL,updated_at=NOW() WHERE user_id=$1 AND mode='personal'",[user.id]);
  await cx.query('UPDATE telegram_personal_dialogs SET enabled=FALSE WHERE user_id=$1',[user.id]);
  await cx.query('UPDATE telegram_listener_keys SET revoked_at=NOW() WHERE user_id=$1 AND revoked_at IS NULL',[user.id]);
  await cx.query('COMMIT');
  return answer(res,200,{disconnected:true,worker_revoked:true,live_trade_execution:false});
 }catch{await cx?.query('ROLLBACK').catch(()=>{});return answer(res,503,{error:'disconnect_unavailable'})}
 finally{cx?.release()}
};
