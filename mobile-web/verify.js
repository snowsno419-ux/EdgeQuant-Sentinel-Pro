'use strict';
const $=id=>document.getElementById(id),msg=t=>$('status').textContent=t;
const token=new URLSearchParams(location.hash.replace(/^#/, '')).get('token');history.replaceState(null,'',location.pathname);
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
$('verify').onclick=async()=>{try{if(!token)throw Error('Verification token missing or expired');await post('/api/verify-email',{token});$('verify').hidden=true;$('totp-setup').style.display='block';msg('Email verified. Now set up your authenticator.') }catch(e){msg(e.message)}};
$('create').onclick=async()=>{try{const j=await post('/api/totp-setup',{});$('secret').value=j.secret;$('totp-confirm').style.display='block';msg('Add secret to authenticator and enter its 6-digit code.')}catch(e){msg(e.message)}};
$('confirm').onclick=async()=>{try{await post('/api/totp-confirm',{code:$('code').value.trim()});$('secret').value='';$('code').value='';$('totp-setup').style.display='none';$('totp-confirm').style.display='none';msg('2FA activated. Return to EdgeQuant and sign in.')}catch(e){msg(e.message)}};
