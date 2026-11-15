'use strict';
const {answer}=require('./_lib/core');
const handlers=Object.freeze({
 'channels':require('./_lib/routes/channels'),
 'telegram-observation':require('./_lib/routes/telegram-observation'),
 'telegram-inbox':require('./_lib/routes/telegram-inbox'),
 'telegram-listener-requests':require('./_lib/routes/telegram-listener-requests')
});
module.exports=async function(req,res){const key=String(req.query?.action||new URL(req.url||'/','https://example.invalid').searchParams.get('action')||'');const fn=Object.hasOwn(handlers,key)?handlers[key]:null;return fn?fn(req,res):answer(res,404,{error:'unknown_telegram_action'})};
