'use strict';
const {randomBytes}=require('node:crypto');
const {sha,answer}=require('../core');
const {db}=require('../db');
const {sameOrigin}=require('../registry');
const {canSendTo}=require('../mail-policy');
const {normalizeEmail,validEmail,readyForPasswordReset,sendPasswordReset}=require('../password-reset');
const {throttle}=require('../onboarding');
module.exports=async function(req,res){
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const body=req.body;
 if(!body||typeof body!=='object'||Array.isArray(body)||Object.keys(body).join(',')!=='email')return answer(res,400,{error:'invalid_request'});
 const email=normalizeEmail(body.email);
 if(!validEmail(email))return answer(res,400,{error:'invalid_request'});
 if(!readyForPasswordReset()||!db())return answer(res,503,{error:'password_recovery_not_configured'});
 const generic={check_email:true,live_trade_execution:false};
 try{
  // Every email (including non-existent ones) consumes the same request allowance.
  const pool=db();
  if(!await throttle(pool,'password-reset-request:'+email,3,3600))return answer(res,202,generic);
  if(!canSendTo(email))return answer(res,202,generic);
  const q=await pool.query('SELECT id FROM users WHERE email=$1 AND email_verified=TRUE AND totp_secret IS NOT NULL',[email]);
  if(!q.rowCount)return answer(res,202,generic);
  const token=randomBytes(32).toString('base64url');
  const digest=sha(token),userId=q.rows[0].id;
  await pool.query("INSERT INTO password_reset_tokens(token_digest,user_id,expires_at) VALUES($1,$2,NOW()+INTERVAL '20 minutes') ON CONFLICT(user_id) DO UPDATE SET token_digest=EXCLUDED.token_digest,expires_at=EXCLUDED.expires_at",[digest,userId]);
  try{await sendPasswordReset(email,token)}catch{
   await pool.query('DELETE FROM password_reset_tokens WHERE token_digest=$1',[digest]).catch(()=>{});
  }
  return answer(res,202,generic);
 }catch{
  return answer(res,503,{error:'password_recovery_unavailable'});
 }
};
