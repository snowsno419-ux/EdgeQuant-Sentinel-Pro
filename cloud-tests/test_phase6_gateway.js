'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const base=path.resolve(__dirname,'../mobile-web');
const rules=require(path.join(base,'vercel.json')).rewrites||[];
const endpoints=['signup','resend-verification','verify-email','totp-setup','totp-confirm','channels','telegram-observation','telegram-inbox'];
test('Vercel Hobby function count <=12',()=>{assert.ok(fs.readdirSync(path.join(base,'api')).filter(x=>x.endsWith('.js')).length<=12)});
test('all legacy onboarding and telegram URLs correctly route through serverless gateway',()=>{
 for(const e of endpoints){const rule=rules.find(r=>r.source==='/api/'+e);assert.ok(rule,'missing rewrite '+e);assert.equal(rule.destination,'/api/'+(['signup','resend-verification','verify-email','totp-setup','totp-confirm'].includes(e)?'auth':'telegram')+'?action='+e);assert.ok(fs.existsSync(path.join(base,'api/_lib/routes/'+e+'.js')))}
});
test('unknown action rejected (no arbitrary module loading)',async()=>{const req={method:'POST',query:{action:'../../../secret'},headers:{}};const res={status(n){this.statusCode=n;return this},setHeader(){},json(j){this.result=j;return this}};await require('../mobile-web/api/auth.js')(req,res);assert.equal(res.statusCode,404);assert.equal(res.result.error,'unknown_auth_action')});
