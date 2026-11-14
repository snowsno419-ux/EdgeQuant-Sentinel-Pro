'use strict';
const {answer}=require('./_lib/core');
const handlers=Object.freeze({
 'signup':require('./_lib/routes/signup'),
 'resend-verification':require('./_lib/routes/resend-verification'),
 'verify-email':require('./_lib/routes/verify-email'),
 'totp-setup':require('./_lib/routes/totp-setup'),
 'totp-confirm':require('./_lib/routes/totp-confirm')
});
module.exports=async function(req,res){const key=String(req.query?.action||new URL(req.url||'/','https://example.invalid').searchParams.get('action')||'');const fn=Object.hasOwn(handlers,key)?handlers[key]:null;return fn?fn(req,res):answer(res,404,{error:'unknown_auth_action'})};
