'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {generateKeyPairSync,sign}=require('node:crypto');
const BOT=require('../mobile-web/api/_lib/telegram-bot');
const PAIR=require('../mobile-web/api/_lib/mt5-pair')._validation;

const env={EQ_TELEGRAM_BOT_ENABLED:'1',EQ_TELEGRAM_BOT_TOKEN:'123456789:ABCDefGhIJklMnOPrstUvWxYz_123456789',EQ_TELEGRAM_BOT_WEBHOOK_SECRET:'A_long_test_only_secret_1234567890_abcdef'};
test('Telegram bot mode is disabled by default and secret uses constant-time comparison',()=>{
 assert.equal(BOT.botReady({}),false);
 assert.equal(BOT.botReady(env),true);
 assert.equal(BOT.checkWebhookSecret(env.EQ_TELEGRAM_BOT_WEBHOOK_SECRET,env),true);
 assert.equal(BOT.checkWebhookSecret('wrong_telegram_webhook_secret_123456789',env),false);
 assert.equal(BOT.checkWebhookSecret(env.EQ_TELEGRAM_BOT_WEBHOOK_SECRET,{...env,EQ_TELEGRAM_BOT_ENABLED:'0'}),false);
});
test('Channel posts, edits and private text are parsed with type and numeric chat ID',()=>{
 const original={update_id:42,channel_post:{chat:{id:-1001234567890,type:'channel'},message_id:11,date:1794733300,text:'GOLD BUY 4025 SL 4020 TP 4030'}};
 const p=BOT.parseUpdate(original);
 assert.equal(p.chat_id,'-1001234567890');
 assert.equal(p.kind,'channel_post');
 assert.equal(p.edit_date_ms,0);
 assert.equal(p.message_id,11);
 const edited={update_id:43,edited_channel_post:{chat:{id:-1001234567890,type:'channel'},message_id:11,date:1794733300,edit_date:1794733400,text:'GOLD BUY 4025 SL 4021 TP 4030'}};
 const e=BOT.parseUpdate(edited);
 assert.equal(e.kind,'edited_channel_post');
 assert.equal(e.edit_date_ms,1794733400000);
 assert.equal(BOT.parseUpdate({update_id:1,channel_post:{chat:{id:7,type:'channel'},message_id:1,date:1794733300,text:'x'}}).kind,'ignored');
});
test('Chat ownership requires channel posts or verified group admin identity',async()=>{
 const chan=BOT.parseUpdate({update_id:1,channel_post:{chat:{id:-1001234567890,type:'channel'},message_id:3,date:1794733300,text:'EQVERIFY-'+'A'.repeat(32)}});
 assert.equal(await BOT.groupAdminProof(chan,env),true);
 assert.equal(await BOT.groupAdminProof({...chan,kind:'message',chat_type:'private'},env),false);
});
test('Only a possession-proven Ed25519 worker may claim pairing',()=>{
 const {publicKey,privateKey}=generateKeyPairSync('ed25519');
 const token='A'.repeat(43),worker_id='worker_1234567890123456',login_hint='12345678',server='ICMarketsSC-Demo';
 const text=PAIR.proofText(token,worker_id,server,login_hint);
 const payload={token,worker_id,server,login_hint,public_key_pem:publicKey.export({format:'pem',type:'spki'}).toString(),signature:sign(null,Buffer.from(text),privateKey).toString('base64')};
 const good=PAIR.validateClaim(payload);
 assert.ok(good);
 assert.equal(good.worker_id,worker_id);
 assert.equal(PAIR.validateClaim({...payload,login_hint:'87654321'}),null);
 assert.equal(PAIR.validateClaim({...payload,signature:'bad'}),null);
 assert.equal(PAIR.validateClaim({...payload,unknown:true}),null);
 assert.equal(PAIR.fingerprint(good.public_key_pem).length,24);
});
