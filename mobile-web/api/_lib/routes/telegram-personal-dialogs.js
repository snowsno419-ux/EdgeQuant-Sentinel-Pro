'use strict';
// Account-scoped personal Telegram dialog selection, populated ONLY by a signed worker.
const {answer}=require('../core');
const {db,signedIn}=require('../db');
const {sameOrigin}=require('../registry');
const ID=/^-?[0-9]{5,20}$/;
module.exports=async(req,res)=>{
 if(!['GET','POST'].includes(req.method))return answer(res,405,{error:'method_not_allowed'});
 if(req.method==='POST'&&!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
 try{
  const user=await signedIn(req);if(!user)return answer(res,401,{error:'sign_in_required'});
  if(req.method==='GET'){
   const request=await pool.query('SELECT state,mode,last_seen_at FROM telegram_listener_requests WHERE user_id=$1',[user.id]);
   const a=request.rows[0];
   const recent=a?.last_seen_at&&new Date(a.last_seen_at).getTime()>Date.now()-10*60*1000;
   const dialogs=await pool.query("SELECT chat_id,label,dialog_type,enabled,last_discovered_at FROM telegram_personal_dialogs WHERE user_id=$1 ORDER BY label LIMIT 200",[user.id]);
   return answer(res,200,{connection:a?{state:a.state,mode:a.mode,worker_online:Boolean(a.state==='CONNECTED'&&recent),last_seen_at:a.last_seen_at}:null,dialogs:dialogs.rows,live_trade_execution:false,mtproto_account_login:false});
  }
  const b=req.body;
  if(!b||Array.isArray(b)||typeof b!=='object'||Object.keys(b).sort().join(',')!=='chat_id,enabled'||typeof b.chat_id!=='string'||!ID.test(b.chat_id)||typeof b.enabled!=='boolean')
   return answer(res,400,{error:'invalid_dialog_selection'});
  if(b.enabled){
   const r=await pool.query("SELECT 1 FROM telegram_listener_requests WHERE user_id=$1 AND mode='personal' AND state='CONNECTED' AND last_seen_at>NOW()-INTERVAL '10 minutes'",[user.id]);
   if(!r.rowCount)return answer(res,409,{error:'personal_listener_offline'});
  }
  const q=await pool.query("UPDATE telegram_personal_dialogs SET enabled=$3 WHERE user_id=$1 AND chat_id=$2 AND ($3=FALSE OR last_discovered_at>NOW()-INTERVAL '10 minutes') RETURNING chat_id,enabled",[user.id,b.chat_id,b.enabled]);
  if(!q.rowCount)return answer(res,409,{error:'dialog_unavailable_or_stale'});
  return answer(res,200,{selected:q.rows[0],signals_auto_executed:false,live_trade_execution:false});
 }catch{return answer(res,503,{error:'personal_dialogs_unavailable'})}
};
