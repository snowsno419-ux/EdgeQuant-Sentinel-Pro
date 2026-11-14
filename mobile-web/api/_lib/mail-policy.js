'use strict';
// Shared resend.dev sender is restricted to the email of the Resend account.
// Never allow production-wide signup using a shared test sender.
const EMAIL=/^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;
function normalizeEmail(value){return typeof value==='string'?value.trim().toLowerCase():''}
function senderAddress(from){
 if(typeof from!=='string'||from.length>200)return null;
 const s=from.trim(),m=s.match(/<([^<>]+)>$/);
 const address=(m?m[1]:s).trim().toLowerCase();
 return EMAIL.test(address)?address:null;
}
function mailPolicy(env=process.env){
 const sender=senderAddress(env.EQ_MAIL_FROM);
 const testMode=env.EQ_SIGNUP_TEST_ONLY==='1';
 const sharedSender=sender==='onboarding@resend.dev';
 const recipient=normalizeEmail(env.EQ_TEST_EMAIL);
 if(!sender)return {ready:false,testOnly:testMode||sharedSender};
 if(testMode||sharedSender){
  if(!testMode||!sharedSender||!EMAIL.test(recipient))return {ready:false,testOnly:true};
  return {ready:true,testOnly:true,recipient};
 }
 if(sender.endsWith('@resend.dev'))return {ready:false,testOnly:true};
 return {ready:true,testOnly:false};
}
function canSendTo(email,env=process.env){
 const policy=mailPolicy(env),recipient=normalizeEmail(email);
 return policy.ready&&EMAIL.test(recipient)&&(!policy.testOnly||recipient===policy.recipient);
}
module.exports={mailPolicy,canSendTo,senderAddress};
