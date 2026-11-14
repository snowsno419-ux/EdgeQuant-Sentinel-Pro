'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {mailPolicy,canSendTo}=require('../mobile-web/api/_lib/mail-policy');
const base={EQ_MAIL_FROM:'EdgeQuant Test <onboarding@resend.dev>',EQ_SIGNUP_TEST_ONLY:'1',EQ_TEST_EMAIL:'demo@example.com'};
test('Resend shared sender permits only explicitly allowlisted account email',()=>{
 const p=mailPolicy(base);assert.equal(p.ready,true);assert.equal(p.testOnly,true);
 assert.equal(canSendTo(' DEMO@EXAMPLE.COM ',base),true);
 for(const address of ['other@example.com','delivered@resend.dev','bounced@resend.dev'])assert.equal(canSendTo(address,base),false);
});
test('Shared test sender never operates in public registration mode',()=>{
 assert.equal(mailPolicy({...base,EQ_SIGNUP_TEST_ONLY:'0'}).ready,false);
 assert.equal(mailPolicy({...base,EQ_TEST_EMAIL:''}).ready,false);
 assert.equal(mailPolicy({...base,EQ_TEST_EMAIL:'not an email'}).ready,false);
 assert.equal(canSendTo('demo@example.com',{...base,EQ_TEST_EMAIL:''}),false);
});
test('Other resend.dev senders are not allowed',()=>{
 assert.equal(mailPolicy({EQ_MAIL_FROM:'no-reply@resend.dev'}).ready,false);
 assert.equal(mailPolicy({EQ_MAIL_FROM:'EdgeQuant <onboarding@resend.dev>',EQ_SIGNUP_TEST_ONLY:'1'}).ready,false);
});
test('Verified-domain mode preserves future real registrations',()=>{
 const live={EQ_MAIL_FROM:'EdgeQuant <verify@edgequantpro.com>',EQ_SIGNUP_TEST_ONLY:'0'};
 assert.equal(mailPolicy(live).ready,true);
 assert.equal(canSendTo('any@othermail.com',live),true);
 assert.equal(mailPolicy({...live,EQ_SIGNUP_TEST_ONLY:'1',EQ_TEST_EMAIL:'demo@example.com'}).ready,false);
});
test('Malformed sender is rejected',()=>{
 for(const from of ['', 'EdgeQuant <broken-address>','onboarding@resend.dev\nX-Test:1'])assert.equal(mailPolicy({EQ_MAIL_FROM:from}).ready,false);
});
