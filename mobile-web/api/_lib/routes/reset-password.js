'use strict';
const {sha,answer,passwordValid,totpValid}=require('../core');
const {db}=require('../db');
const {sameOrigin}=require('../registry');
const {decryptTotp,throttle,pwhash}=require('../onboarding');
const {validNewPassword,validResetToken,readyForPasswordReset}=require('../password-reset');
module.exports=async function(req,res){
 if(req.method!=='POST')return answer(res,405,{error:'method_not_allowed'});
 if(!sameOrigin(req))return answer(res,403,{error:'invalid_origin'});
 const b=req.body;
 if(!b||typeof b!=='object'||Array.isArray(b)||Object.keys(b).sort().join(',')!=='code,new_password,token'
 ||!validResetToken(b.token)||!validNewPassword(b.new_password)||typeof b.code!=='string'||!/^\d{6}$/.test(b.code))
  return answer(res,400,{error:'invalid_reset_request'});
 if(!readyForPasswordReset()||!db())return answer(res,503,{error:'password_recovery_not_configured'});
 const digest=sha(b.token);
 let client;
 try{
  client=await db().connect();
  await client.query('BEGIN');
  const result=await client.query('SELECT r.user_id,u.password_hash,u.totp_secret FROM password_reset_tokens r JOIN users u ON u.id=r.user_id WHERE r.token_digest=$1 AND r.expires_at>NOW() AND u.email_verified=TRUE FOR UPDATE OF r,u',[digest]);
  if(!result.rowCount){
   await client.query('ROLLBACK');
   return answer(res,400,{error:'invalid_or_expired_reset_link'});
  }
  const permitted=await throttle(client,'password-reset-attempt:'+digest,5,3600);
  if(!permitted){
   await client.query('COMMIT');
   return answer(res,429,{error:'too_many_reset_attempts'});
  }
  const u=result.rows[0];
  const secret=decryptTotp(u.totp_secret);
  if(!secret||!totpValid(secret,b.code)||passwordValid(b.new_password,u.password_hash)){
   await client.query('COMMIT'); // Persist throttling even on rejected attempts
   return answer(res,400,{error:'invalid_reset_credentials'});
  }
  await client.query('UPDATE users SET password_hash=$2,failed_logins=0,locked_until=NULL WHERE id=$1',[u.user_id,pwhash(b.new_password)]);
  await client.query('DELETE FROM sessions WHERE user_id=$1',[u.user_id]);
  await client.query('DELETE FROM password_reset_tokens WHERE user_id=$1',[u.user_id]);
  await client.query('COMMIT');
  res.setHeader('Set-Cookie','__Host-eq_session=; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=0');
  return answer(res,200,{reset:true,login_required:true,live_trade_execution:false});
 }catch{
  if(client)await client.query('ROLLBACK').catch(()=>{});
  return answer(res,503,{error:'password_recovery_unavailable'});
 }finally{client?.release()}
};
