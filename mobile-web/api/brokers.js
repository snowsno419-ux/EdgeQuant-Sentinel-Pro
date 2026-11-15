'use strict';
// Verified-user broker metadata only. There is no broker-login or trading operation.
const {randomUUID}=require('node:crypto');
const {answer}=require('./_lib/core');
const {db,signedIn}=require('./_lib/db');
const {parseBrokerMetadata,sameOrigin}=require('./_lib/registry');
const MAX_BROKERS_PER_USER=10;
module.exports=async function(req,res){
 const action=typeof req.query?.action==='string'?req.query.action:'';
 if(action.startsWith('pair-'))return require('./_lib/mt5-pair')(req,res,action.slice(5));
  if(!['GET','POST'].includes(req.method))return answer(res,405,{error:'method_not_allowed'});
  const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
  if(req.method==='POST'&&(!sameOrigin(req)||!/^application\/json(?:\s*;|$)/i.test(String(req.headers['content-type']||''))))return answer(res,403,{error:'invalid_request_origin_or_type'});
  try{
    const user=await signedIn(req);
    if(!user)return answer(res,401,{error:'sign_in_required'});
    if(req.method==='GET'){
      const r=await pool.query(`SELECT id,label,broker,server,right(login_hint,4) AS masked_login,created_at
        FROM broker_accounts WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2`,[user.id,MAX_BROKERS_PER_USER]);
      return answer(res,200,{brokers:r.rows.map(x=>({id:x.id,label:x.label,broker:x.broker,server:x.server,login_hint:'••••'+x.masked_login,created_at:x.created_at})),mode:'READ_ONLY'});
    }
    const details=parseBrokerMetadata(req.body);
    if(!details)return answer(res,400,{error:'invalid_demo_broker_metadata'});
    let cx;
    try{
      cx=await pool.connect();await cx.query('BEGIN');
      // Serialize concurrent registry writes per user, in addition to the DB UNIQUE constraint.
      await cx.query('SELECT pg_advisory_xact_lock(hashtext($1))',[user.id]);
      const count=await cx.query('SELECT count(*)::int AS n FROM broker_accounts WHERE user_id=$1',[user.id]);
      if(count.rows[0].n>=MAX_BROKERS_PER_USER){await cx.query('ROLLBACK');return answer(res,409,{error:'broker_limit_reached'})}
      const id=randomUUID();
      await cx.query(`INSERT INTO broker_accounts (id,user_id,label,broker,server,login_hint)
          VALUES ($1,$2,$3,$4,$5,$6)`,[id,user.id,details.label,details.broker,details.server,details.login]);
      await cx.query('COMMIT');
      return answer(res,201,{id,label:details.label,broker:details.broker,server:details.server,login_hint:'••••'+details.login.slice(-4),status:'OFFLINE',worker_provisioned:false,live_trade_execution:false});
    }catch(e){if(cx)try{await cx.query('ROLLBACK')}catch{};if(e?.code==='23505')return answer(res,409,{error:'broker_already_registered'});throw e}
    finally{if(cx)cx.release()}
  }catch{return answer(res,503,{error:'registry_unavailable'})}
};
