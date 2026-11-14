'use strict';
// Cloud onboarding helpers. Keep secrets in Vercel encrypted envs, never in frontend/GitHub.
const {randomBytes, scryptSync, createCipheriv, createDecipheriv, createHmac}=require('node:crypto');
const {sha}=require('./core');
const EMAIL=/^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;
const B32='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
function validateSignup(x){
 if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).sort().join(',')!=='email,password,role')return null;
 const email=typeof x.email==='string'?x.email.trim().toLowerCase():'';
 if(email.length>254||!EMAIL.test(email)||typeof x.password!=='string'||x.password.length<12||x.password.length>128||!['receiver','provider'].includes(x.role))return null;
 if(!/[A-Za-z]/.test(x.password)||!/[0-9]/.test(x.password))return null;
 return {email,password:x.password,role:x.role};
}
function pwhash(p){const salt=randomBytes(16);return 'scrypt$'+salt.toString('hex')+'$'+scryptSync(p,salt,64,{N:16384,r:8,p:1}).toString('hex')}
function b32(buf){let bits=0,n=0,out='';for(const b of buf){bits=(bits<<8)|b;n+=8;while(n>=5){n-=5;out+=B32[(bits>>n)&31]}}if(n)out+=B32[(bits<<(5-n))&31];return out}
function secretKey(){const h=process.env.EQ_TOTP_ENCRYPTION_KEY;return typeof h==='string'&&/^[0-9a-fA-F]{64}$/.test(h)?Buffer.from(h,'hex'):null}
function encryptTotp(secret){const key=secretKey();if(!key)throw Error('TOTP encryption not configured');const iv=randomBytes(12),cipher=createCipheriv('aes-256-gcm',key,iv);const enc=Buffer.concat([cipher.update(secret,'utf8'),cipher.final()]);return ['v1',iv.toString('hex'),cipher.getAuthTag().toString('hex'),enc.toString('hex')].join(':')}
function decryptTotp(x){try{const key=secretKey();if(!key||typeof x!=='string')return null;const p=x.split(':');if(p.length!==4||p[0]!=='v1'||!/^[a-f0-9]{24}$/.test(p[1])||!/^[a-f0-9]{32}$/.test(p[2]))return null;const c=createDecipheriv('aes-256-gcm',key,Buffer.from(p[1],'hex'));c.setAuthTag(Buffer.from(p[2],'hex'));return Buffer.concat([c.update(Buffer.from(p[3],'hex')),c.final()]).toString('utf8')}catch{return null}}
function readyForRegistration(){return Boolean(process.env.EQ_SIGNUP_ENABLED==='1'&&process.env.DATABASE_URL&&process.env.RESEND_API_KEY&&process.env.EQ_MAIL_FROM&&/^https:\/\/[a-zA-Z0-9.-]+$/.test(process.env.EQ_PUBLIC_ORIGIN||'')&&secretKey())}
function cookie(name,val,maxAge){return `${name}=${val}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=${maxAge}`}
async function throttle(db,key,limit,secs){const k=sha(key);const q=await db.query(`INSERT INTO auth_throttle(bucket,hits,window_start) VALUES($1,1,NOW()) ON CONFLICT(bucket) DO UPDATE SET hits=CASE WHEN auth_throttle.window_start < NOW()-($2::int * INTERVAL '1 second') THEN 1 ELSE auth_throttle.hits+1 END, window_start=CASE WHEN auth_throttle.window_start < NOW()-($2::int * INTERVAL '1 second') THEN NOW() ELSE auth_throttle.window_start END RETURNING hits`,[k,secs]);return q.rows[0].hits<=limit}
async function sendVerify(email,token){const url=process.env.EQ_PUBLIC_ORIGIN+'/verify.html#token='+encodeURIComponent(token);const controller=new AbortController();const tid=setTimeout(()=>controller.abort(),7500);try{const response=await fetch('https://api.resend.com/emails',{method:'POST',signal:controller.signal,headers:{Authorization:'Bearer '+process.env.RESEND_API_KEY,'Content-Type':'application/json'},body:JSON.stringify({from:process.env.EQ_MAIL_FROM,to:[email],subject:'Verify your EdgeQuant DEMO account',text:'Open this verification link and click Verify. Expires in 20 minutes: '+url})});if(!response.ok)throw Error('Email provider rejected request')}finally{clearTimeout(tid)}}
function notReady(res,answer){return answer(res,503,{error:'registration_not_configured',mode:'NO_LIVE_TRADING'})}
module.exports={validateSignup,pwhash,b32,encryptTotp,decryptTotp,readyForRegistration,cookie,throttle,sendVerify,notReady};
