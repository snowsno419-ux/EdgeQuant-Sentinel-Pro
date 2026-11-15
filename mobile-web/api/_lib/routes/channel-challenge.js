'use strict';
const {randomBytes}=require('node:crypto'),{answer,sha}=require('../core');
const {db,signedIn}=require('../db'),{sameOrigin}=require('../registry'),{throttle}=require('../onboarding');
const {chatId,botReady}=require('../telegram-bot');
module.exports=async(req,res)=>{
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const b=req.body;if(!b||typeof b!=='object'||Array.isArray(b)||Object.keys(b).join(',')!=='chat_id'||!chatId(b.chat_id))return answer(res,400,{error:'invalid_chat_id'});
 if(!botReady())return answer(res,503,{error:'telegram_bot_not_configured'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 try{
  const user=await signedIn(req);if(!user)return answer(res,401,{error:'sign_in_required'});
  const c=await pool.query('SELECT verified_at FROM telegram_sources WHERE user_id=$1 AND chat_id=$2',[user.id,b.chat_id]);
  if(!c.rowCount)return answer(res,404,{error:'source_not_registered'});
  if(c.rows[0].verified_at&&new Date(c.rows[0].verified_at).getTime()>Date.now()-30*86400000)return answer(res,409,{error:'source_already_verified'});
  if(!await throttle(pool,'channel-proof:'+user.id,5,3600))return answer(res,429,{error:'too_many_requests'});
  const code='EQVERIFY-'+randomBytes(16).toString('hex').toUpperCase();
  await pool.query("INSERT INTO telegram_source_claims(user_id,chat_id,code_digest,expires_at) VALUES($1,$2,$3,NOW()+INTERVAL '15 minutes') ON CONFLICT(user_id,chat_id) DO UPDATE SET code_digest=EXCLUDED.code_digest,expires_at=EXCLUDED.expires_at",[user.id,b.chat_id,sha(code)]);
  return answer(res,200,{proof_code:code,expires_in_seconds:900,method:'POST_AS_CHAT_ADMIN',telegram_connected:false,live_trade_execution:false});
 }catch{return answer(res,503,{error:'channel_proof_unavailable'})}
};
