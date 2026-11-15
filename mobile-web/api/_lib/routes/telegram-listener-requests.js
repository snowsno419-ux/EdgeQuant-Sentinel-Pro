'use strict';
// Account-scoped request for managed, read-only Telegram listener provisioning.
// This endpoint DOES NOT perform Telegram login or accept credentials.
const {answer}=require('../core');
const {db,signedIn}=require('../db');
const {sameOrigin}=require('../registry');
const {throttle}=require('../onboarding');
module.exports=async function(req,res){
 if(req.method!=='GET'&&req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(req.method==='POST'&&!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 if(req.method==='POST'&&(!req.body||Array.isArray(req.body)||typeof req.body!=='object'||Object.keys(req.body).length!==0))return answer(res,400,{error:'invalid_request'});
 const pool=db();
 if(!pool)return answer(res,503,{error:'database_not_configured'});
 try{
  const user=await signedIn(req);
  if(!user)return answer(res,401,{error:'sign_in_required'});
  if(req.method==='GET'){
   const q=await pool.query('SELECT id,state,mode,last_seen_at,created_at,updated_at FROM telegram_listener_requests WHERE user_id=$1',[user.id]);
   return answer(res,200,{request:q.rows[0]||null,telegram_connected:false,live_trade_execution:false});
  }
  if(!await throttle(pool,'telegram-listener-request:'+user.id,8,3600))return answer(res,429,{error:'too_many_requests'});
  const q=await pool.query("INSERT INTO telegram_listener_requests(user_id,state,mode) VALUES($1,'PENDING','personal') ON CONFLICT(user_id) DO UPDATE SET updated_at=NOW(),mode='personal' RETURNING id,state,mode,last_seen_at,created_at,updated_at",[user.id]);
  return answer(res,202,{request:q.rows[0],note:'Personal Telegram listener requested. Approval and an encrypted per-user cloud listener are still required. No phone number, OTP or Telegram password was collected.',telegram_connected:false,live_trade_execution:false});
 }catch{return answer(res,503,{error:'telegram_listener_request_unavailable'})}
};
