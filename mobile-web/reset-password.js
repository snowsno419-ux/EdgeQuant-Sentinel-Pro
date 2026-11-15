'use strict';
const form=document.getElementById('reset-form'),status=document.getElementById('status'),button=document.getElementById('submit');
const params=new URLSearchParams(location.hash.slice(1)),token=params.get('token');
history.replaceState(null,'',location.pathname);
if(!token||!/^[A-Za-z0-9_-]{43}$/.test(token)){
 status.textContent='Reset link is missing or invalid. Request a new email link.';
}else{
 form.hidden=false;
 status.textContent='Enter a new password and your current authenticator code.';
}
form.addEventListener('submit',async e=>{
 e.preventDefault();
 const new_password=document.getElementById('new-password').value;
 const confirm=document.getElementById('confirm-password').value;
 const code=document.getElementById('code').value.trim();
 if(new_password!==confirm){status.textContent='Passwords do not match.';return}
 if(new_password.length<12||new_password.length>128||!/[A-Za-z]/.test(new_password)||!/[0-9]/.test(new_password)){
  status.textContent='Use 12–128 characters including letters and numbers.';return
 }
 if(!/^\d{6}$/.test(code)){status.textContent='Enter the 6-digit Google Authenticator code.';return}
 button.disabled=true;status.textContent='Verifying your request…';
 try{
  const r=await fetch('/api/reset-password',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,new_password,code})});
  const result=await r.json();
  if(!r.ok){
   if(r.status===429)throw Error('Too many attempts. Request a new link later.');
   if(r.status===503)throw Error('Recovery service is unavailable. Please try later.');
   throw Error('Reset link or authenticator code is invalid, or the password was already used.');
  }
  document.getElementById('new-password').value='';
  document.getElementById('confirm-password').value='';
  document.getElementById('code').value='';
  form.hidden=true;
  status.textContent='Password updated. Sign in with the new password and your authenticator code.';
 }catch(err){status.textContent=err.message||'Reset could not be completed.'}
 finally{button.disabled=false}
});
