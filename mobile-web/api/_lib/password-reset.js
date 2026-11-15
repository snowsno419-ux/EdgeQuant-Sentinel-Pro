'use strict';
// Password reset tokens are never exposed in logs or JSON responses.
const EMAIL=/^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;
const {mailPolicy}=require('./mail-policy');
function normalizeEmail(value){return typeof value==='string'?value.trim().toLowerCase():''}
function validEmail(value){return value.length<=254&&EMAIL.test(value)}
function validNewPassword(value){return typeof value==='string'&&value.length>=12&&value.length<=128&&/[A-Za-z]/.test(value)&&/[0-9]/.test(value)}
function validResetToken(value){return typeof value==='string'&&/^[A-Za-z0-9_-]{43}$/.test(value)}
function readyForPasswordReset(env=process.env){
 return Boolean(env.EQ_PASSWORD_RESET_ENABLED!=='0'&&env.DATABASE_URL&&env.RESEND_API_KEY
   &&/^https:\/\/[a-zA-Z0-9.-]+$/.test(env.EQ_PUBLIC_ORIGIN||'')&&mailPolicy(env).ready);
}
async function sendPasswordReset(email,token,env=process.env){
 const url=env.EQ_PUBLIC_ORIGIN+'/reset-password.html#token='+encodeURIComponent(token);
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),7500);
 try{
  const response=await fetch('https://api.resend.com/emails',{
   method:'POST',signal:controller.signal,
   headers:{Authorization:'Bearer '+env.RESEND_API_KEY,'Content-Type':'application/json'},
   body:JSON.stringify({
    from:env.EQ_MAIL_FROM,to:[email],subject:'EdgeQuant password reset request',
    text:'A request was made to reset your EdgeQuant DEMO account password. If this was you, open this link within 20 minutes: '+url+
    '\nIf you did not request a reset, ignore this email. Your existing password and authenticator stay active.'
   })
  });
  if(!response.ok)throw Error('email_delivery_unavailable');
 }finally{clearTimeout(timer)}
}
module.exports={normalizeEmail,validEmail,validNewPassword,validResetToken,readyForPasswordReset,sendPasswordReset};
