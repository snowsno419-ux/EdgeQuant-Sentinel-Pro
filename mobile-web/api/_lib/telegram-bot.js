'use strict';
// A bot added to an authorized chat can receive only updates Telegram forwards to that bot.
// Never confuse Bot API integration with account-wide Telegram/MTProto login.
const {timingSafeEqual}=require('node:crypto');
const SECRET=/^[A-Za-z0-9_-]{32,256}$/;
const TOKEN=/^\d{5,15}:[A-Za-z0-9_-]{30,100}$/;
function botReady(env=process.env){return env.EQ_TELEGRAM_BOT_ENABLED==='1'&&SECRET.test(env.EQ_TELEGRAM_BOT_WEBHOOK_SECRET||'')&&TOKEN.test(env.EQ_TELEGRAM_BOT_TOKEN||'')}
function checkWebhookSecret(input,env=process.env){const expected=env.EQ_TELEGRAM_BOT_WEBHOOK_SECRET;if(!botReady(env)||typeof input!=='string'||!SECRET.test(input))return false;const a=Buffer.from(input),b=Buffer.from(expected);return a.length===b.length&&timingSafeEqual(a,b)}
function chatId(value){const s=typeof value==='number'&&Number.isSafeInteger(value)?String(value):typeof value==='string'?value:'';return /^-?\d{5,20}$/.test(s)?s:null}
function parseUpdate(x){
 if(!x||typeof x!=='object'||Array.isArray(x)||!Number.isSafeInteger(x.update_id)||x.update_id<0)return null;
 const kind=x.channel_post?'channel_post':x.edited_channel_post?'edited_channel_post':x.message?'message':x.edited_message?'edited_message':null;
 if(!kind)return {update_id:x.update_id,kind:'ignored'};
 const m=x[kind],cid=chatId(m?.chat?.id);
 if(!cid||!Number.isSafeInteger(m?.message_id)||m.message_id<=0)return {update_id:x.update_id,kind:'ignored'};
 const raw=typeof m.text==='string'?m.text:typeof m.caption==='string'?m.caption:'';
 const date=Number.isSafeInteger(m.edit_date)?m.edit_date:Number.isSafeInteger(m.date)?m.date:0;
 if(!date||!raw||raw.length>3000||/[\u0000-\u0008\u000b-\u001f\u007f]/.test(raw))return {update_id:x.update_id,kind:'ignored'};
 return {update_id:x.update_id,kind,chat_id:cid,chat_type:m.chat.type,text:raw,message_id:m.message_id,
 reply_to_id:Number.isSafeInteger(m.reply_to_message?.message_id)?m.reply_to_message.message_id:0,
 edit_date_ms:kind.startsWith('edited_')?Number.isSafeInteger(m.edit_date)?m.edit_date*1000:date*1000:0,
 observed_at_ms:date*1000,
 sender_id:Number.isSafeInteger(m.from?.id)?m.from.id:null,
 sender_chat_id:chatId(m.sender_chat?.id)};
}
async function groupAdminProof(event,env=process.env){
 if(event.chat_type==='channel'&&event.kind==='channel_post')return true; // only channel admins can post
 if(event.chat_type!=='group'&&event.chat_type!=='supergroup')return false;
 if(event.sender_chat_id===event.chat_id)return true; // sent as group, admin-only identity
 if(!Number.isSafeInteger(event.sender_id)||!botReady(env))return false;
 const ctrl=new AbortController(),id=setTimeout(()=>ctrl.abort(),3500);
 try{
  const token=env.EQ_TELEGRAM_BOT_TOKEN;
  const url='https://api.telegram.org/bot'+token+'/getChatMember';
  const r=await fetch(url,{method:'POST',signal:ctrl.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:event.chat_id,user_id:event.sender_id})});
  if(!r.ok)return false;
  const j=await r.json();
  return j.ok===true&&['creator','administrator'].includes(j.result?.status);
 }catch{return false}finally{clearTimeout(id)}
}
async function respondChatId(event,env=process.env){
 if(!botReady(env))return false;
 const ctrl=new AbortController(),timeout=setTimeout(()=>ctrl.abort(),4000);
 try{
  const r=await fetch('https://api.telegram.org/bot'+env.EQ_TELEGRAM_BOT_TOKEN+'/sendMessage',{
   method:'POST',signal:ctrl.signal,headers:{'Content-Type':'application/json'},
   body:JSON.stringify({chat_id:event.chat_id,text:'EdgeQuant Chat ID: '+event.chat_id+'\nRegister this ID in your verified EdgeQuant app. No trading is enabled.'})
  });
  return r.ok;
 }catch{return false}finally{clearTimeout(timeout)}
}
module.exports={botReady,checkWebhookSecret,chatId,parseUpdate,groupAdminProof,respondChatId};
