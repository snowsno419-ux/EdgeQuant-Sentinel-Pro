'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const P=require('../mobile-web/api/_lib/password-reset');
const TEST_ENV={
 DATABASE_URL:'postgres://example.invalid/db',RESEND_API_KEY:'example-do-not-use',
 EQ_MAIL_FROM:'EdgeQuant Test <onboarding@resend.dev>',
 EQ_PUBLIC_ORIGIN:'https://edgequant-mobile-web.vercel.app',
 EQ_SIGNUP_TEST_ONLY:'1',EQ_TEST_EMAIL:'owner@example.com'
};
test('Password reset is restricted to configured sender and current test recipient',()=>{
 assert.equal(P.readyForPasswordReset(TEST_ENV),true);
 assert.equal(P.readyForPasswordReset({...TEST_ENV,RESEND_API_KEY:''}),false);
 assert.equal(P.readyForPasswordReset({...TEST_ENV,EQ_SIGNUP_TEST_ONLY:'0'}),false);
 assert.equal(P.readyForPasswordReset({...TEST_ENV,EQ_TEST_EMAIL:''}),false);
 assert.equal(P.readyForPasswordReset({...TEST_ENV,EQ_PASSWORD_RESET_ENABLED:'0'}),false);
 assert.equal(P.readyForPasswordReset({...TEST_ENV,EQ_PUBLIC_ORIGIN:'http://localhost'}),false);
});
test('Email format, password complexity, token shape are validated',()=>{
 assert.equal(P.normalizeEmail(' OWNER@EXAMPLE.COM '),'owner@example.com');
 assert.equal(P.validEmail(P.normalizeEmail(' OWNER@EXAMPLE.COM ')),true);
 for(const e of ['','bad','broken@','test@site'])assert.equal(P.validEmail(e),false);
 for(const p of ['123456789012','letters-only-long','AB1','a'.repeat(129)+'1'])assert.equal(P.validNewPassword(p),false);
 assert.equal(P.validNewPassword('Secure-Temporary-2026'),true);
 assert.equal(P.validResetToken('A'.repeat(43)),true);
 for(const t of ['A'.repeat(42),'A'.repeat(44),'a'.repeat(20)+'?'])assert.equal(P.validResetToken(t),false);
});
test('Recovery email uses HTTPS link with hash, only the designated recipient',async()=>{
 const original=global.fetch;
 let observed=null;
 try{
  global.fetch=async(url,options)=>{observed={url,options};return {ok:true}};
  await P.sendPasswordReset('owner@example.com','TEST_TOKEN_NOT_REAL_12345678901234567890123',TEST_ENV);
  assert.equal(observed.url,'https://api.resend.com/emails');
  assert.equal(observed.options.method,'POST');
  const body=JSON.parse(observed.options.body);
  assert.deepEqual(body.to,['owner@example.com']);
  assert.match(body.text,/https:\/\/edgequant-mobile-web\.vercel\.app\/reset-password\.html#token=/);
  assert.equal(body.text.includes('api/login'),false);
 }finally{global.fetch=original}
});
