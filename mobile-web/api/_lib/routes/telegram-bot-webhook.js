'use strict';
const {answer,sha}=require('../core'),{db}=require('../db');
const {checkWebhookSecret,parseUpdate,groupAdminProof,respondChatId}=require('../telegram-bot');
module.exports=async(req,res)=>{
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!checkWebhookSecret(req.headers['x-telegram-bot-api-secret-token']))return answer(res,401,{error:'unauthorized'});
 if(!/^application\/json(?:\s*;|$)/i.test(String(req.headers['content-type']||'')))return answer(res,415,{error:'invalid_content_type'});
 if(!req.body||typeof req.body!=='object'||Array.isArray(req.body)||JSON.stringify(req.body).length>20000)return answer(res,400,{error:'invalid_update'});
 const event=parseUpdate(req.body);
 if(!event)return answer(res,400,{error:'invalid_update'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 let cx;
 try{
  cx=await pool.connect();await cx.query('BEGIN');
  const u=await cx.query('INSERT INTO telegram_bot_updates(update_id) VALUES($1) ON CONFLICT DO NOTHING RETURNING update_id',[event.update_id]);
  if(!u.rowCount){await cx.query('COMMIT');return answer(res,200,{ok:true,duplicate:true})}
  if(event.kind==='ignored'){await cx.query('COMMIT');return answer(res,200,{ok:true,ignored:true})}
  if(/^\/eqid(?:@[a-zA-Z0-9_]+)?$/i.test(event.text.trim())){
   if(await groupAdminProof(event))await respondChatId(event);
   await cx.query('COMMIT');return answer(res,200,{ok:true,admin_command:true});
  }
  const proof=event.text.trim().match(/^EQVERIFY-[A-F0-9]{32}$/);
  if(proof){
   // Only channel posts or verified group admins may prove authorization.
   if(await groupAdminProof(event)){
    const claim=await cx.query('DELETE FROM telegram_source_claims WHERE chat_id=$1 AND code_digest=$2 AND expires_at>NOW() RETURNING user_id',[event.chat_id,sha(proof[0])]);
    if(claim.rowCount){
     await cx.query('UPDATE telegram_sources SET verified_at=NOW(),enabled=FALSE WHERE user_id=$1 AND chat_id=$2',[claim.rows[0].user_id,event.chat_id]);
    }
   }
   await cx.query('COMMIT');return answer(res,200,{ok:true,claim_processed:true});
  }
  const kind=event.kind.startsWith('edited_')?'edit':'new';
  const ins=await cx.query("INSERT INTO telegram_inbox(user_id,chat_id,message_id,reply_to_id,edit_date_ms,kind,body,observed_at_ms) SELECT s.user_id,$1,$2,$3,$4,$5,$6,$7 FROM telegram_sources s WHERE s.chat_id=$1 AND s.enabled=TRUE AND s.verified_at>NOW()-INTERVAL '30 days' ON CONFLICT(user_id,chat_id,message_id,edit_date_ms) DO NOTHING RETURNING user_id",[event.chat_id,event.message_id,event.reply_to_id,event.edit_date_ms,kind,event.text,event.observed_at_ms]);
  if(ins.rowCount)await cx.query("UPDATE telegram_sources SET last_observed_at=NOW() WHERE chat_id=$1 AND enabled=TRUE AND verified_at>NOW()-INTERVAL '30 days'",[event.chat_id]);
  await cx.query('COMMIT');
  return answer(res,200,{ok:true,received:true,live_trade_execution:false});
 }catch{
  if(cx)await cx.query('ROLLBACK').catch(()=>{});
  return answer(res,503,{error:'telegram_webhook_unavailable'});
 }finally{cx?.release()}
};
