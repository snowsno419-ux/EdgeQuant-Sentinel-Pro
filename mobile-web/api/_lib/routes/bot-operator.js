'use strict';
// Server-side Bot API operator controls. Bot token and webhook secret never leave Vercel.
// During test-only signup, the configured Resend test inbox owner may configure the bot;
// public mode requires explicit EQ_BOT_OPERATOR_EMAIL env.
const {answer}=require('../core'),{db,signedIn}=require('../db'),{sameOrigin}=require('../registry');
const {botReady}=require('../telegram-bot');
const {throttle}=require('../onboarding');
function operatorEmail(env=process.env){
 const raw=env.EQ_BOT_OPERATOR_EMAIL||(env.EQ_SIGNUP_TEST_ONLY==='1'?env.EQ_TEST_EMAIL:'');
 return typeof raw==='string'?raw.toLowerCase().trim():'';
}
function operatorAllowed(user,env=process.env){
 const email=operatorEmail(env);
 return Boolean(email&&user?.email?.toLowerCase()===email);
}
async function method(name,body){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7000);
 try{
  const url='https://api.telegram.org/bot'+process.env.EQ_TELEGRAM_BOT_TOKEN+'/'+name;
  const r=await fetch(url,{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
  if(!r.ok)throw Error('telegram_api_unavailable');
  const data=await r.json();
  if(data.ok!==true)throw Error('telegram_api_rejected');
  return data.result;
 }finally{clearTimeout(timer)}
}
module.exports=async function(req,res,action){
 if(!['bot-info','bot-setup'].includes(action))return answer(res,404,{error:'unknown_action'});
 if(req.method!==(action==='bot-info'?'GET':'POST'))return answer(res,405,{error:'method_not_allowed'});
 if(action==='bot-setup'&&(!sameOrigin(req)||!req.body||typeof req.body!=='object'||Array.isArray(req.body)||Object.keys(req.body).length))
  return answer(res,403,{error:'invalid_request_origin'});
 if(!botReady())return answer(res,503,{error:'telegram_bot_not_configured'});
 if(!db())return answer(res,503,{error:'database_not_configured'});
 try{
  const user=await signedIn(req);
  if(!user)return answer(res,401,{error:'sign_in_required'});
  const allowed=operatorAllowed(user);
  const url=process.env.EQ_PUBLIC_ORIGIN+'/api/telegram-bot-webhook';
  if(!/^https:\/\/[a-z0-9.-]+\.vercel\.app\/api\/telegram-bot-webhook$/.test(url))
   return answer(res,503,{error:'invalid_public_origin'});
  if(action==='bot-setup'){
   if(!allowed)return answer(res,403,{error:'operator_only'});
   if(!await throttle(db(),'bot-webhook-operator:'+user.id,3,3600))return answer(res,429,{error:'too_many_requests'});
   await method('setWebhook',{url,secret_token:process.env.EQ_TELEGRAM_BOT_WEBHOOK_SECRET,
    allowed_updates:['message','edited_message','channel_post','edited_channel_post'],drop_pending_updates:false,max_connections:10});
  }
  const [info,webhook]=await Promise.all([method('getMe'),method('getWebhookInfo')]);
  return answer(res,200,{bot_username:typeof info?.username==='string'?info.username:null,
   webhook_active:webhook?.url===url,
   pending_updates:Number.isSafeInteger(webhook?.pending_update_count)?webhook.pending_update_count:null,
   can_setup:allowed,mode:'BOT_READ_ONLY',live_trade_execution:false});
 }catch{return answer(res,503,{error:'telegram_bot_service_unavailable'})}
};
