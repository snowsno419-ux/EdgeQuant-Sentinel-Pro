'use strict';
const {answer}=require('../core'),{db,signedIn}=require('../db'),{sameOrigin}=require('../registry'),{botReady,chatId}=require('../telegram-bot');
module.exports=async(req,res)=>{
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const b=req.body;
 if(!b||typeof b!=='object'||Array.isArray(b)||Object.keys(b).sort().join(',')!=='chat_id,enabled'||!chatId(b.chat_id)||typeof b.enabled!=='boolean')
  return answer(res,400,{error:'invalid_request'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 try{
  const u=await signedIn(req);if(!u)return answer(res,401,{error:'sign_in_required'});
  if(b.enabled&&!botReady())return answer(res,503,{error:'telegram_bot_not_configured'});
  const q=await pool.query('UPDATE telegram_sources SET enabled=$3 WHERE user_id=$1 AND chat_id=$2 AND ($3=FALSE OR verified_at IS NOT NULL) RETURNING chat_id,enabled,verified_at',[u.id,b.chat_id,b.enabled]);
  if(!q.rowCount)return answer(res,409,{error:'source_missing_or_not_verified'});
  return answer(res,200,{chat_id:q.rows[0].chat_id,enabled:q.rows[0].enabled,verified:!!q.rows[0].verified_at,live_trade_execution:false});
 }catch{return answer(res,503,{error:'channel_toggle_unavailable'})}
};
