'use strict';
const form=document.getElementById('forgot-form'),status=document.getElementById('status'),button=document.getElementById('submit');
form.addEventListener('submit',async e=>{
 e.preventDefault();button.disabled=true;status.textContent='Processing request…';
 try{
  const email=document.getElementById('email').value.trim();
  const r=await fetch('/api/forgot-password',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});
  const result=await r.json();
  if(!r.ok)throw Error(r.status===503?'Password recovery is not configured yet. Please try later.':r.status===429?'Too many attempts. Please try later.':'Unable to process this request.');
  status.textContent='If this verified account is eligible, a reset link will arrive by email. Check Spam too.';
 }catch(e){status.textContent=e.message||'Please try again later.'}
 finally{button.disabled=false}
});
