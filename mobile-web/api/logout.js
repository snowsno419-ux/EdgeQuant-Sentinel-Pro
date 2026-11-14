'use strict';
// Revoke the active session immediately. No destructive MT5 action is possible.
const {answer,sha,parseCookies}=require('./_lib/core');
const {db}=require('./_lib/db');
const {sameOrigin}=require('./_lib/registry');
module.exports=async function(req,res){
  if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
  if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
  const pool=db();if(!pool)return answer(res,503,{error:'database_not_configured'});
  try{
    const token=parseCookies(req.headers.cookie)['__Host-eq_session'];
    if(token&&/^[A-Za-z0-9_-]{30,200}$/.test(token))await pool.query('DELETE FROM sessions WHERE token_digest=$1',[sha(token)]);
    res.setHeader('Set-Cookie','__Host-eq_session=; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=0');
    return answer(res,200,{ok:true,live_trade_execution:false});
  }catch{return answer(res,503,{error:'logout_unavailable'})}
};
