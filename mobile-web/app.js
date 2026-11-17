/* EdgeQuant Sentinel Pro PC-style responsive UI — static, client-only DEMO.
   Do not add broker passwords, real login or trade execution endpoints here. */
'use strict';
const GROUPS=[
 {title:'TRADING WORKSPACE',items:[['dashboard','Dashboard','ඩෑෂ්බෝඩ්'],['channels','Channels','චැනල්ස්'],['brokers','Brokers / MT5','බ්‍රෝකර්ස් / MT5'],['journal','Trade Journal','ගනුදෙනු සටහන්']]},
 {title:'ORDERS & PERFORMANCE',items:[['progress','Channel Progress','චැනල් ප්‍රගතිය'],['manual','Manual Trades','අතින් කළ ගනුදෙනු'],['calendar','Profit Calendar','ලාභ දින දර්ශනය'],['plan','Trading Plan','ගනුදෙනු සැලැස්ම']]},
 {title:'TOOLS & SETTINGS',items:[['profile','Login / Register','පිවිසීම / ලියාපදිංචිය'],['studio','Signal Studio','සිග්නල් ස්ටුඩියෝ'],['advanced','Advanced','උසස් සැකසුම්'],['preview','Signal Preview','සිග්නල් පෙරදසුන'],['activity','Activity','ක්‍රියාකාරකම්'],['settings','Settings','සැකසුම්'],['guide','Guide / Upades','මාර්ගෝපදේශය'],['welcome','Workspace setup','වැඩ අවකාශ සැකසුම']]}
];
const SUBTITLE={dashboard:'Your account, today\'s performance and live activity at a glance.',channels:'Manage the Telegram sources monitored by your client.',brokers:'Review and manage the connected MT5 account list.',journal:'Search full trade history and inspect live or pending tickets.',progress:'Realized results and trade outcomes, grouped by signal source.',manual:'Non-EdgeQuant MT5 trades opened today.',calendar:'Daily realized results across the selected period.',plan:'Review risk assumptions and plan parameters before trading.',profile:'Sign in or create your secure EdgeQuant cloud account.',studio:'Compose, review and publish signals to selected destinations.',advanced:'Voice, reporting and specialist controls.',preview:'Check how an incoming message is parsed before processing.',activity:'Diagnostics, confirmations and worker messages.',settings:'Configure local strategy and application preferences.',guide:'Role-specific Provider and Receiver instructions.',welcome:'Choose the workspace role you want to preview.'};
const DEFAULT={role:'receiver',language:'EN',theme:'neon',voice:'SI',lot:0.01,layers:2,tp1:50,maxTrades:10,be:false,bePips:50,beLock:0,partial:false,partialPips:50,partialPercent:50,partialLayer:true,trailing:false,trailStart:25,trailDistance:10,hold:'KEEP_TP',dailyTarget:0,dailyLoss:0,lossEnabled:false,targetEnabled:false,agent:false,manualConfirm:true,telegramAlert:false,spreadMax:0,channels:[],brokers:[],reportPeriod:'today'};
const LS_KEY='edgequant_pc_web_v2_draft_only';
function readDraft(){try{const x=JSON.parse(localStorage.getItem(LS_KEY)||'{}');if(!x||typeof x!=='object')return {...DEFAULT};return {...DEFAULT,...x,channels:Array.isArray(x.channels)?x.channels:[],brokers:Array.isArray(x.brokers)?x.brokers:[]};}catch{return {...DEFAULT}}}
const prefs=readDraft();
const cloud={reachable:false,database:false,registration:false,telegramInboxReady:false,workerRequestsReady:false,telegramRequestReady:false,telegramPersonalReady:false,telegramPersonal:{connection:null,dialogs:[]},telegramRequest:null,telegramConnected:false,telegramBotReady:false,telegramBotInfo:null,mt5PairingReady:false,mt5WorkerConnected:false,authChecked:false,channels:[],inbox:[],authenticated:false,user:null,snapshot:null,lastError:null};
let page='profile',authTab='login',simulation=false,selectedDate=null,calDate=new Date(),toastTimer=null,log=[{date:new Date(),title:'Web preview started',detail:'Cloud trading service is NOT connected. Account metrics are unavailable.'}],filter='all',lastProof=null,lastPairing=null,pairStatus={};
const $=q=>document.querySelector(q); const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function save(){localStorage.setItem(LS_KEY,JSON.stringify(prefs))}
function slt(d=new Date()){return new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Colombo',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(d)+' SLT'}
function note(){return '<div class="notice">⚠ READ-ONLY CLOUD STAGE — MT5 DEMO metrics require verified login and signed Windows worker data. All trading controls here are browser-only drafts; no MT5 order actions are available.</div>'}
function btn(text,action='draft-save',type='btn-outline',extra=''){return `<button class="btn ${type}" data-action="${esc(action)}" type="button" ${extra}>${text}</button>`}
function field(label,key,type='number',opt=''){const val=prefs[key];return `<label class="field"><span>${label}</span><input type="${type}" data-pref="${key}" value="${esc(val)}" ${opt}></label>`}
function select(label,key,opts){return `<label class="field"><span>${label}</span><select data-pref="${key}">${opts.map(([v,t])=>`<option value="${esc(v)}" ${String(prefs[key])===String(v)?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`}
function check(label,key){return `<label class="switch-label"><input type="checkbox" data-pref="${key}" ${prefs[key]?'checked':''}><span>${label}</span></label>`}
function surface(title,content,sub='',cls=''){return `<section class="surface ${cls}"><div class="panel-title">${title}</div>${sub?`<p class="panel-sub">${sub}</p>`:''}${content}</section>`}
function sectionHeading(label,meta=''){return `<div class="section-head"><b class="small-caps">${label}</b><span class="text-note">${meta}</span></div>`}
function empty(t='No live MT5 data available'){return `<div class="empty">${t}</div>`}
function metric(label,value,accent='cyan',extra=''){let col={cyan:'var(--cyan)',mint:'var(--mint)',purple:'var(--purple)',amber:'var(--amber)'}[accent];return `<div class="metric" style="--accent:${col}"><span>${label}</span><strong class="${extra}">${value}</strong></div>`}
function cloudAccounts(){return Array.isArray(cloud.snapshot?.brokers)?cloud.snapshot.brokers:[]}
function currentBroker(){return cloudAccounts().find(x=>x.status==='CONNECTED')||null}
function cloudVal(value,asMoney=false){if(value===null||value===undefined||!Number.isFinite(Number(value)))return '—';return asMoney?Number(value).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}):String(value)}

function realBrokerSummary(){
 const bs=cloudAccounts();
 if(!bs.length)return empty(cloud.database?'No DEMO broker registered. Add one below first.':'Cloud database unavailable.');
 return '<div class="activity-list">'+bs.map(b=>{
  const p=pairStatus[b.id]?.pairing;
  const token=lastPairing?.broker_id===b.id&&lastPairing.expires_at>Date.now()?lastPairing.token:null;
  const actionButtons='<div class="option-list">'+
   (cloud.workerRequestsReady&&b.status!=='CONNECTED'?btn('REQUEST MANAGED CLOUD WORKER','cloud-worker-request:'+b.id,'btn-muted'):'')+
   (cloud.mt5PairingReady?btn('GENERATE PAIRING TOKEN','cloud-pair-start:'+b.id,'btn-primary')+btn('CHECK PAIR STATUS','cloud-pair-status:'+b.id,'btn-muted'):'')+
   (p?.state==='CLAIMED'?btn('APPROVE READ-ONLY WORKER','cloud-pair-approve:'+b.id,'btn-muted'):'')+
   '</div>';
  const pairingInfo=p?'<p class="text-note">Pair: '+esc(p.state)+' • Worker '+esc(p.worker_id||'—')+
   (p.fingerprint?' • Public key fingerprint: <b class="mono">'+esc(p.fingerprint)+'</b>':'')+'</p>':'';
  const tokenBox=token?'<div class="pair-token"><b>Private one-time worker pairing token (15 minutes)</b><input aria-label="Pairing token" readonly value="'+esc(token)+'" onclick="this.select()"><p class="text-note">Copy only to your authorized Windows cloud worker. Never send the code in chat or screenshots. Broker ID: <span class="mono">'+esc(b.id)+'</span></p></div>':'';
  return '<div class="activity-item"><div class="activity-dot">●</div><div class="broker-connection"><b>'+esc(b.label)+'</b> <span class="connection-status '+(b.status==='CONNECTED'?'linked':'pending')+'">'+esc(b.status)+'</span><div class="text-note">'+esc(b.broker)+' · '+esc(b.server)+' · account '+esc(b.login_hint)+' · Balance '+cloudVal(b.balance,true)+' · Equity '+cloudVal(b.equity,true)+'</div><small class="muted mono">'+(b.observed_at?esc(slt(new Date(b.observed_at))):'No signed telemetry')+'</small>'+pairingInfo+actionButtons+tokenBox+'</div></div>';
 }).join('')+'</div>';
}
async function checkCloud(){let changed=false;const firstCheck=!cloud.authChecked;const previousAccountId=cloud.user?.id||null;try{const r=await fetch('/api/health',{cache:'no-store',credentials:'same-origin',headers:{Accept:'application/json'}});if(!r.ok)throw Error('Cloud API unavailable');const j=await r.json();const previous=cloud.reachable+':'+cloud.database+':'+cloud.authenticated+':'+(cloud.snapshot?.brokers?.map(x=>[x.id,x.status,x.observed_at].join('-')).join(',')||'')+':'+(cloud.telegramRequest?.state||'')+':'+(cloud.channels?.map(c=>[c.chat_id,c.verified,c.enabled,c.last_observed_at].join('-')).join(',')||'')+':'+(cloud.telegramPersonal?.connection?.state||'')+':'+(cloud.telegramPersonal?.connection?.worker_online||false)+':'+(cloud.telegramPersonal?.dialogs?.map(x=>[x.chat_id,x.enabled].join('-')).join(',')||'');cloud.reachable=j.ok===true;cloud.database=j.database_ready===true;cloud.registration=j.registration_enabled===true;cloud.telegramInboxReady=j.telegram_inbox_ready===true;cloud.workerRequestsReady=j.worker_request_ready===true;cloud.telegramRequestReady=j.telegram_listener_request_ready===true;cloud.telegramPersonalReady=j.telegram_personal_ready===true;cloud.telegramBotReady=j.telegram_bot_configured===true;cloud.mt5PairingReady=j.mt5_pairing_available===true;cloud.telegramConnected=j.telegram_connected===true;cloud.mt5WorkerConnected=j.mt5_worker_connected===true;cloud.authenticated=false;cloud.user=null;cloud.snapshot=null;cloud.telegramRequest=null;cloud.telegramPersonal={connection:null,dialogs:[]};cloud.channels=[];cloud.inbox=[];cloud.lastError=null;
if(cloud.database){const u=await fetch('/api/me',{credentials:'same-origin',cache:'no-store'});if(u.ok){cloud.user=await u.json();cloud.authenticated=true; if(['receiver','provider'].includes(cloud.user?.role))prefs.role=cloud.user.role;if(cloud.telegramInboxReady){const [c,i]=await Promise.all([fetch('/api/channels',{credentials:'same-origin',cache:'no-store'}),fetch('/api/telegram-inbox',{credentials:'same-origin',cache:'no-store'})]);cloud.channels=c.ok?(await c.json()).channels:[];cloud.inbox=i.ok?(await i.json()).messages:[]}if(cloud.telegramRequestReady){try{const tr=await fetch('/api/telegram-listener-requests',{credentials:'same-origin',cache:'no-store'});cloud.telegramRequest=tr.ok?(await tr.json()).request:null}catch{cloud.telegramRequest=null}}if(cloud.telegramPersonalReady){try{const personal=await fetch('/api/telegram-personal-dialogs',{credentials:'same-origin',cache:'no-store'});if(personal.ok)cloud.telegramPersonal=await personal.json()}catch{cloud.telegramPersonal={connection:null,dialogs:[]}}}const d=await fetch('/api/dashboard',{credentials:'same-origin',cache:'no-store'});if(d.ok)cloud.snapshot=await d.json()}}
const now=cloud.reachable+':'+cloud.database+':'+cloud.authenticated+':'+(cloud.snapshot?.brokers?.map(x=>[x.id,x.status,x.observed_at].join('-')).join(',')||'')+':'+(cloud.telegramRequest?.state||'')+':'+(cloud.channels?.map(c=>[c.chat_id,c.verified,c.enabled,c.last_observed_at].join('-')).join(',')||'')+':'+(cloud.telegramPersonal?.connection?.state||'')+':'+(cloud.telegramPersonal?.connection?.worker_online||false)+':'+(cloud.telegramPersonal?.dialogs?.map(x=>[x.chat_id,x.enabled].join('-')).join(',')||'');changed=previous!==now;
}catch(e){changed=cloud.reachable||cloud.authenticated;cloud.reachable=false;cloud.database=false;cloud.registration=false;cloud.authenticated=false;cloud.user=null;cloud.snapshot=null;cloud.telegramRequest=null;cloud.telegramPersonal={connection:null,dialogs:[]};cloud.lastError=String(e).slice(0,100)}
if(!cloud.authenticated||(previousAccountId&&previousAccountId!==cloud.user?.id)){lastPairing=null;lastProof=null;pairStatus={};cloud.telegramBotInfo=null}if(lastProof&&cloud.channels.some(c=>c.chat_id===lastProof.chat_id&&c.verified))lastProof=null;
cloud.authChecked=true;if(firstCheck)changed=true;if(!cloud.authenticated){page='profile';}else if(page==='profile'&&firstCheck){page='dashboard';}
const el=$('#api-health');if(el){el.textContent=!cloud.reachable?'UNAVAILABLE':!cloud.database?'API ONLINE · DB OFF':!cloud.authenticated?'LOGIN REQUIRED':'READ-ONLY ONLINE';el.className=cloud.reachable?'mint':'amber'}
if(changed)render();}
async function cloudLogin(){if(!cloud.reachable||!cloud.database)return message('Secure cloud login is not provisioned yet.');const email=$('#cloud-login-email')?.value.trim(),password=$('#cloud-login-password')?.value,code=$('#cloud-login-code')?.value;try{const r=await fetch('/api/login',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password,code})});if(!r.ok)throw Error('Login failed. Check your account password and current authenticator code.');await checkCloud();if(!cloud.authenticated)throw Error('Could not confirm the secure login session.');nav('dashboard');message('Signed in securely. Welcome to your EdgeQuant dashboard.')}catch(e){message(String(e.message).slice(0,100))}finally{if($('#cloud-login-password'))$('#cloud-login-password').value='';if($('#cloud-login-code'))$('#cloud-login-code').value=''}}
async function cloudResendVerification(){
 if(!cloud.registration)return message('Verification service is not configured.');
 const email=$('#cloud-signup-email')?.value.trim(),password=$('#cloud-signup-password')?.value;
 try{const r=await fetch('/api/resend-verification',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});const j=await r.json();if(!r.ok)throw Error(j.error||'Verification resend not available');message('If this unverified account exists, a new email will arrive.');}
 catch(e){message('Email resend unavailable: '+String(e.message).slice(0,90))}
 finally{if($('#cloud-signup-password'))$('#cloud-signup-password').value=''}
}
async function cloudSignup(){
  if(!cloud.registration)return message('Registration unavailable until private database and verified email delivery are configured.');
  const email=$('#cloud-signup-email')?.value.trim(),password=$('#cloud-signup-password')?.value,role=$('#cloud-signup-role')?.value;
  try{const r=await fetch('/api/signup',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password,role})});const j=await r.json();if(!r.ok)throw Error(j.error||'Signup unavailable');message('Check your email for verification. Complete authenticator setup before login.');}
  catch(e){message('Registration not completed: '+String(e.message).slice(0,100))}
  finally{if($('#cloud-signup-password'))$('#cloud-signup-password').value=''}
}
async function cloudRequestWorker(brokerId){
 if(!cloud.authenticated||!cloud.workerRequestsReady)return message('Managed worker request database is not ready.');
 try{const r=await fetch('/api/worker-requests',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({broker_id:brokerId})});const j=await r.json();if(!r.ok)throw Error(j.error||'Worker request unavailable');message('Windows DEMO worker request saved: '+j.state+'. Operator provisioning still needed; no trades sent.');}
 catch(e){message(String(e.message).slice(0,100))}
}
async function cloudAddChannel(){
 if(!cloud.authenticated||!cloud.telegramInboxReady)return message('Secure channel registry is not available.');
 const raw=$('#tg-cloud-chat')?.value?.trim(),label=$('#tg-cloud-label')?.value?.trim(),kind=$('#tg-cloud-kind')?.value;
 try{const r=await fetch('/api/channels',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:raw,label,kind,enabled:false})});const j=await r.json();if(!r.ok)throw Error(j.error||'Channel not registered');message('Channel metadata registered OFF. Private worker approval required for Telegram monitoring.');await checkCloud();render();}catch(e){message('Channel registration: '+String(e.message).slice(0,100))}
}
async function cloudRequestTelegramListener(){
 if(!cloud.authenticated||!cloud.telegramRequestReady)return message('Cloud Telegram listener request service is unavailable.');
 try{
  const r=await fetch('/api/telegram-listener-requests',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:'{}'});
  const j=await r.json();
  if(!r.ok)throw Error(j.error||'Listener request was not saved');
  cloud.telegramRequest=j.request||null;render();
  message('Personal Telegram cloud listener requested. Operator provisioning is still needed; no OTP or password collected.');
 }catch(e){message('Telegram request: '+String(e.message).slice(0,80))}
}

async function cloudTogglePersonalDialog(chatId,enabled){
 if(!cloud.authenticated||!cloud.telegramPersonalReady)return message('Personal Telegram listener is not ready.');
 try{
  const r=await fetch('/api/telegram-personal-dialogs',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:chatId,enabled})});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Source change rejected');
  await checkCloud();render();
  message(enabled?'Source enabled for read-only inbox. Trading OFF.':'Personal Telegram source disabled.');
 }catch(e){message('Telegram channels: '+String(e.message).slice(0,90))}
}
async function cloudDisconnectPersonal(){
 if(!cloud.authenticated||!cloud.telegramPersonalReady)return;
 if(!confirm('Disconnect your personal Telegram cloud listener and revoke its access? This stops message collection.'))return;
 try{
  const r=await fetch('/api/telegram-personal-disconnect',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Disconnect failed');
  await checkCloud();render();message('Personal Telegram worker access revoked. Trading remains OFF.');
 }catch(e){message('Disconnect: '+String(e.message).slice(0,90))}
}
function cloudPersonalTelegram(){
 const connection=cloud.telegramPersonal?.connection;
 const dialogs=Array.isArray(cloud.telegramPersonal?.dialogs)?cloud.telegramPersonal.dialogs:[];
 const isOnline=connection?.worker_online===true;
 const status=isOnline?'WORKER ONLINE':connection?.state==='CONNECTED'?'WORKER OFFLINE / STALE':connection?.state==='PENDING'?'PROVISIONING REQUEST PENDING':connection?.state||'NOT CONNECTED';
 const rows=dialogs.map(c=>{
  const active=isOnline&&c.enabled;
  return `<div class="connection-source"><div><b>${esc(c.label)}</b>
  <span class="connection-status ${active?'linked':'pending'}">${active?'READ-ONLY ON':'OFF'}</span>
  <p class="text-note">${esc(c.dialog_type)} · ${esc(c.chat_id)} · Last discovered ${c.last_discovered_at?esc(slt(new Date(c.last_discovered_at))):'—'}</p>
  <div class="option-list">${c.enabled?btn('TURN OFF','cloud-personal-off:'+c.chat_id,'btn-muted'):(isOnline?btn('ENABLE READ-ONLY','cloud-personal-on:'+c.chat_id,'btn-primary'):'<span class="text-note">Worker must be online first</span>')}</div>
  </div></div>`;
 }).join('');
 return surface('PERSONAL TELEGRAM ACCOUNT · MAIN CONNECTION',`
 <div class="info"><b>Status: ${esc(status)}.</b> This is the main EdgeQuant option. Each client will connect their own Telegram account through an isolated cloud MTProto listener, without creating a Bot.</div>
 <div class="control-group"><b>Step 1 • Request personal cloud listener</b>
 <p class="text-note">After a secure listener has been provisioned, it can authenticate your Telegram account and discover the groups/channels you joined. No phone number, OTP, 2FA password or Telegram session is accepted by this public page yet.</p>
 <div class="option-list">${cloud.telegramRequestReady?btn(connection?.state==='PENDING'?'REQUEST SUBMITTED':'REQUEST PERSONAL TELEGRAM CONNECTION','cloud-telegram-listener-request','btn-primary'):'<span class="text-note">Cloud request service is not ready.</span>'}
 ${btn('REFRESH CONNECTION STATUS','cloud-refresh','btn-muted')}
 ${connection?btn('DISCONNECT & REVOKE','cloud-personal-disconnect','btn-muted'):''}</div>
 <p class="text-note">Listener status: ${esc(connection?.state||'NOT REQUESTED')}; last signed heartbeat: ${connection?.last_seen_at?esc(slt(new Date(connection.last_seen_at))):'none'}.</p></div>
 <div class="control-group"><b>Step 2 • Choose your Telegram groups / channels</b>
 <p class="text-note">Discovered channels will appear automatically only after your separate cloud listener logs in and sends a signed, account-scoped list. Enable only the sources you wish to monitor.</p>
 ${rows||empty('No personal Telegram groups/channels discovered. Worker not yet connected.')}
 </div><div class="notice">Personal Telegram login service is not running yet. This preparation does not make a Telegram connection or execute MT5 trades.</div>
 `, 'Read-only • Per-user session isolation • Zero Telegram credentials in Neon');
}
async function cloudCheckTelegramBot(setup=false){
 if(!cloud.authenticated||!cloud.telegramBotReady)return message('Telegram Bot provider is not configured.');
 try{
  const r=await fetch(setup?'/api/telegram-bot-setup':'/api/telegram-bot-info',
   setup?{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'}:{credentials:'same-origin',cache:'no-store'});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Bot status unavailable');
  cloud.telegramBotInfo=j;render();
  message(j.webhook_active?'Telegram Bot webhook ACTIVE. Add it to your authorized group/channel.':'Bot configured; webhook is NOT active yet.');
 }catch(e){message('Bot status: '+String(e.message).slice(0,90))}
}
async function cloudChannelChallenge(chatId){
 if(!cloud.authenticated||!cloud.telegramBotReady)return message('Telegram Bot bridge is not configured yet.');
 try{
  const r=await fetch('/api/channel-challenge',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:chatId})});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Channel verification unavailable');
  lastProof={chat_id:chatId,code:j.proof_code,expires_at:Date.now()+900000};
  render();message('Post this one-time code in the Telegram chat as an admin within 15 minutes.');
 }catch(e){message('Telegram verification: '+String(e.message).slice(0,85))}
}
async function cloudToggleChannel(chatId,enabled){
 if(!cloud.authenticated)return;
 try{
  const r=await fetch('/api/channel-toggle',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:chatId,enabled})});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Channel switch unavailable');
  await checkCloud();render();
  message(enabled?'Read-only Telegram inbox enabled for verified source. Trading remains OFF.':'Source disabled.');
 }catch(e){message('Source switch: '+String(e.message).slice(0,90))}
}
async function cloudPairStart(brokerId){
 if(!cloud.authenticated||!cloud.mt5PairingReady)return message('MT5 worker pairing is not configured.');
 try{
  const r=await fetch('/api/mt5-pair-start',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({broker_id:brokerId})});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Pair code unavailable');
  lastPairing={broker_id:brokerId,token:j.pairing_token,expires_at:Date.now()+900000};delete pairStatus[brokerId];
  render();message('Private 15-minute pairing token generated. Enter it on your authorized Windows cloud worker.');
 }catch(e){message('MT5 pairing: '+String(e.message).slice(0,85))}
}
async function cloudPairStatus(brokerId){
 if(!cloud.authenticated)return;
 try{
  const r=await fetch('/api/mt5-pair-status?broker_id='+encodeURIComponent(brokerId),{credentials:'same-origin',cache:'no-store'});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Pairing status unavailable');
  pairStatus[brokerId]=j;render();
  message(j.worker_registered?'Read-only worker key is registered. Signed MT5 telemetry is required for CONNECTED status.':j.pairing?.state==='CLAIMED'?'Worker claim received. Verify fingerprint before approval.':'Pairing status refreshed.');
 }catch(e){message('MT5 status: '+String(e.message).slice(0,85))}
}
async function cloudPairApprove(brokerId){
 const p=pairStatus[brokerId]?.pairing;
 if(!p||p.state!=='CLAIMED'||!p.fingerprint)return message('Check pending worker claim first.');
 if(!confirm('Approve this read-only MT5 worker only after matching its fingerprint with the private Windows worker?'))return;
 try{
  const r=await fetch('/api/mt5-pair-approve',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({broker_id:brokerId})});
  const j=await r.json();if(!r.ok)throw Error(j.error||'Approval unavailable');
  lastPairing=null;await cloudPairStatus(brokerId);
  message('Worker public key approved. Account remains OFFLINE until real signed DEMO telemetry arrives. Trading OFF.');
 }catch(e){message('MT5 approval: '+String(e.message).slice(0,80))}
}

async function cloudRegisterBroker(){
  if(!cloud.authenticated||!cloud.database)return message('A verified cloud login and database are required. No account saved.');
  const label=$('#cloud-broker-label')?.value?.trim(),broker=$('#cloud-broker-name')?.value?.trim(),server=$('#cloud-broker-server')?.value?.trim(),login=$('#cloud-broker-login')?.value?.trim();
  if(!label||!broker||!server||!/^\d{4,18}$/.test(login||''))return message('Provide DEMO broker label, broker, exact server and account number. Never enter a password.');
  try{
    const r=await fetch('/api/brokers',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({label,broker,server,login,mode:'DEMO'})});
    const j=await r.json();
    if(!r.ok)throw Error(j.error||'Registry unavailable');
    message('DEMO account metadata registered. Status OFFLINE until a signed Windows worker is assigned.');
    await checkCloud();render();
  }catch(e){message('Broker registration not completed: '+String(e.message).slice(0,80))}
  finally{const x=$('#cloud-broker-login');if(x)x.value=''}
}
async function cloudLogout(){
  if(!cloud.authenticated)return message('No cloud session to close.');
  try{const r=await fetch('/api/logout',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw Error('Could not close server session');await checkCloud();nav('profile');message('Cloud session signed out. No trades were changed.')}
  catch(e){message(String(e.message).slice(0,90))}
}
function cloudBrokerRegistration(){
  if(!cloud.authenticated)return surface('REGISTER A CLOUD DEMO BROKER',empty('Sign in to a verified cloud account to register broker metadata. Registration is not enabled until private PostgreSQL is connected.'),'No MT5 password or trading operations accepted');
  return surface('REGISTER DEMO ACCOUNT · CLOUD METADATA',`<div class="info">Save the exact broker DEMO server and account number, then an operator must provision its separate read-only MT5 worker. This form NEVER logs into MT5.</div><div class="form-row"><label class="field"><span>ACCOUNT LABEL</span><input id="cloud-broker-label" maxlength="64" placeholder="My IC DEMO"></label><label class="field"><span>BROKER NAME</span><input id="cloud-broker-name" maxlength="64" placeholder="IC Markets"></label><label class="field wide"><span>EXACT DEMO SERVER</span><input id="cloud-broker-server" maxlength="100" placeholder="ICMarketsSC-Demo"></label><label class="field wide"><span>DEMO ACCOUNT NUMBER (NO PASSWORD)</span><input id="cloud-broker-login" maxlength="18" inputmode="numeric" autocomplete="off" placeholder="DEMO account number"></label>${btn('SAVE DEMO ACCOUNT METADATA','cloud-broker-register','btn-primary')}</div><p class="text-note">Only verified-user metadata is stored in the private database. No worker is automatically connected; trading remains OFF.</p>`);
}

function connectionSetup(){
 const sources=Array.isArray(cloud.channels)?cloud.channels:[];
 const accounts=cloudAccounts();
 const active=accounts.filter(b=>b.status==='CONNECTED').length;
 const personal=cloud.telegramPersonal?.connection;
 const online=personal?.worker_online===true;
 const personalSourceCount=cloud.telegramPersonal?.dialogs?.length||0;
 const botReceiving=sources.some(c=>c.enabled===true&&c.verified===true&&c.last_observed_at&&Date.now()-new Date(c.last_observed_at).getTime()<600000);
 return `<section class="connection-setup" aria-label="Cloud connection setup">
 <div class="connection-heading"><div><span class="small-caps">SIGNED IN · ${esc(cloud.user?.role||'account').toUpperCase()}</span><h2>Welcome to EdgeQuant</h2><p>${esc(cloud.user?.email||'Verified account')} · Configure authorized connections for this account.</p></div><span class="status-pill">TRADING OFF</span></div>
 <div class="connection-cards">
 <div class="connection-card"><div class="connection-card-top"><span class="connection-emoji">✈</span><span class="connection-status ${online||botReceiving?'linked':'pending'}">${online?'PERSONAL LISTENER ONLINE':botReceiving?'BOT MESSAGES RECEIVING':'NOT CONNECTED'}</span></div>
 <h3>Personal Telegram</h3><p>${personalSourceCount} account channels discovered. ${online?'Private listener is online.':'Connect each client Telegram account via an isolated cloud listener. Provisioning is pending.'} Bot mode remains optional.</p>
 ${btn('SET UP TELEGRAM','nav:channels','btn-primary')}<small>Personal Telegram is the primary workflow. The cloud account listener must be hosted separately. Trading OFF.</small></div>
 <div class="connection-card"><div class="connection-card-top"><span class="connection-emoji">▣</span><span class="connection-status ${active?'linked':'pending'}">${active?active+' DEMO CONNECTED':'NOT CONNECTED'}</span></div>
 <h3>MetaTrader 5</h3><p>${accounts.length} DEMO broker${accounts.length===1?'':'s'} registered. A signed Windows cloud worker is required; this phone does not run MT5 itself.</p>
 ${btn('SET UP MT5','nav:brokers','btn-primary')}<small>Read-only worker pairing; no MT5 passwords or order execution.</small></div>
 </div></section>`;
}
function dashboard(){return `${connectionSetup()}<section class="surface accent-top">
 ${sectionHeading('NEON DARK / COMMAND CENTER','SIGNED MT5 DEMO DATA ONLY • READ ONLY')}
 <div class="metric-grid">${metric('BALANCE',cloudVal(currentBroker()?.balance,true))}${metric('EQUITY',cloudVal(currentBroker()?.equity,true),'mint')}${metric('FLOATING P&L',cloudVal(currentBroker()?.floating,true),'purple')}${metric('PENDING ORDERS',cloudVal(currentBroker()?.pending_orders))}${metric('OPEN TRADES',cloudVal(currentBroker()?.open_positions),'amber')}${metric('MT5 STATUS',currentBroker()?'DEMO CONNECTED':'OFFLINE','mint',currentBroker()?'':'offline')}</div>
 <div class="over-section"><div><b class="small-caps">LIVE TRADING CONTROL CENTER</b><div class="panel-title" style="font-size:21px">Trading overview</div><div class="subline">MT5 STATUS • VERIFIED SIGNED DEMO REPORTS ONLY</div><div class="text-note">${currentBroker()?`Broker ${esc(currentBroker().broker)} | Account ${esc(currentBroker().login_hint)}<br><b class="cyan">Balance ${cloudVal(currentBroker().balance,true)} · Equity ${cloudVal(currentBroker().equity,true)}</b>`:'Broker — | Account —<br><b class="cyan">Balance — · Equity —</b>'}</div></div><div class="over-actions">${btn('CHANNELS','nav:channels')}${btn('TRADE JOURNAL','nav:journal')}${btn("TODAY'S REPORT",'nav:plan','btn-primary')}</div></div>
 <div class="control-bar"><label>LOT SIZE / LAYER <input data-pref="lot" type="number" min="0.01" max="100" step="0.01" value="${prefs.lot}"></label><label>LAYERS / ENTRY <input data-pref="layers" type="number" min="1" max="8" step="1" value="${prefs.layers}"></label>${btn('APPLY LAYERS','draft-save','btn-muted')}${btn('APPLY LOT','draft-save','btn-muted')}<span class="text-note">NEXT: ${Number(prefs.layers)} × ${Number(prefs.lot).toFixed(2)} lots/entry • draft only</span></div>
 ${controlsProtection()}</section>
 <div class="setting-grid"><div>${surface('BROKER INTELLIGENCE / MAIN + EXTRA',`${sectionHeading('MULTI-BROKER ACCOUNTS')}${realBrokerSummary()}${btn('REFRESH ACCOUNTS','offline-info')} ${btn('BROKERS / MT5','nav:brokers','btn-muted')}`)}</div><div>${surface('XAUUSD / MARKET WATCH',`${sectionHeading('LIVE SPREAD & PRICE')}${metric('XAUUSD  •  LIVE PRICE','—','cyan')}<div class="form-row">${field('MAX SPREAD (PIPS)','spreadMax','number','min="0" step="0.1"')}${btn('APPLY LIMIT','draft-save')}</div><div class="text-note">Market quote / EMA 20–50 / Bid / Ask / Spread • waiting for real MT5 data</div>`)}</div></div>
 ${surface('LIVE TRADES & PENDING ORDERS',`${sectionHeading('OPEN POSITIONS / PENDING / CANCELLED','Worker connection required')}${empty('Live order list is unavailable until a secure worker is connected. No simulated tickets are displayed.')}${btn('VIEW TRADE JOURNAL','nav:journal')}`)}
 ${surface('TODAY’S ACCOUNT SUMMARY',`${sectionHeading('DAILY TARGET & LOSS LIMIT')}${check('DAILY LOSS LIMIT ON/OFF','lossEnabled')} ${check('DAILY TARGET ON/OFF','targetEnabled')}<div class="form-row">${field('DAILY LOSS LIMIT ($)','dailyLoss','number','min="0" step="1"')}${field('DAILY TARGET ($)','dailyTarget','number','min="0" step="1"')}${btn('SAVE DAILY LIMITS','draft-save')}</div>${empty('Today’s realized P&L cannot be calculated until MT5 is connected.')}`)}
 ${surface('CHANNEL PERFORMANCE / DAILY SIGNALS',`${sectionHeading('LIMIT / MARKET SOURCE COUNTS')}${empty('No Telegram channels connected. Signal counts, triggered positions, TP/SL and pending status are offline.')}${btn('GO TO CHANNELS','nav:channels')}`)}
 `}
function controlsProtection(){return `<div class="control-group" style="border-top:2px solid var(--purple)">${sectionHeading('TRADE PROTECTION / TRAILING • BREAK EVEN • HOLD','UI draft controls')}
 <div class="option-list">${check('AUTO BE ON/OFF','be')}${check('BE AFTER TP1 (requires Auto BE)','manualConfirm')}${check('TRAILING STOP ON','trailing')}</div>
 <div class="form-row">${field('BE AT +PIPS','bePips','number','min="1" step="1"')}${field('LOCK +PIPS','beLock','number','min="0" step="1"')}${field('TRAIL START (PIPS)','trailStart','number','min="0"')}${field('TRAIL DISTANCE (PIPS)','trailDistance','number','min="0.1" step="0.1"')}${btn('SAVE PROTECTION','draft-save')}</div>
 <div class="option-list"><span class="thin-title amber">Telegram BE AND HOLD →</span><label><input type="radio" name="hold" data-pref="hold" value="KEEP_TP" ${prefs.hold==='KEEP_TP'?'checked':''}>KEEP TP</label><label><input type="radio" name="hold" data-pref="hold" value="REMOVE_TP" ${prefs.hold==='REMOVE_TP'?'checked':''}>REMOVE TP / HOLD</label>${btn('SAVE HOLD CHOICE','draft-save','btn-muted')}</div>
 <hr class="hline"><div class="form-row"><label class="field wide"><span>OPEN TRADE</span><select disabled><option>Select a running trade (offline)</option></select></label>${btn('SHOW 3 BE POSITIONS','offline-info','btn-muted')}${btn('TP OFF / HOLD','offline-info','btn-muted')}${btn('TP ON / SET','offline-info','btn-muted')}</div>
 <div class="small-caps" style="margin:8px 0">MANUAL PARTIAL CLOSE / AUTO PARTIAL</div><div class="option-list">${check('PARTIAL CLOSE ON/OFF','partial')}${check('AUTO 0.01: QUICK-LAYER FALLBACK','partialLayer')}</div><div class="form-row">${field('PROFIT +PIPS','partialPips','number','min="1"')}${field('CLOSE %','partialPercent','number','min="1" max="99"')}${btn('APPLY PARTIAL','draft-save','btn-muted')}${btn('PREVIEW + CONFIRM MANUAL PARTIAL','offline-info','btn-muted')}</div>
 <div class="text-note">BE suggestions must use a real market quote and selected entry. No live quote, no trade modification. Broker lot minimum and confirmation rules are not simulated here.</div></div>`}


function cloudTelegram(){
 const sources=Array.isArray(cloud.channels)?cloud.channels:[];
 const recent=Array.isArray(cloud.inbox)?cloud.inbox:[];
 const botInfo=cloud.telegramBotReady?'<div class="control-group"><b>Platform Bot Setup</b><p class="text-note">'+
  (cloud.telegramBotInfo?.bot_username?'Bot username: <b>@'+esc(cloud.telegramBotInfo.bot_username)+'</b> · ':'')+
  'Webhook: '+(cloud.telegramBotInfo?.webhook_active?'ACTIVE':'NOT VERIFIED')+'</p><div class="option-list">'+
  btn('CHECK BOT STATUS','cloud-bot-info','btn-muted')+
  (cloud.telegramBotInfo?.can_setup?btn('INITIALIZE BOT WEBHOOK','cloud-bot-setup','btn-primary'):'')+
  '</div></div>':'';
 const all=sources.map(c=>{
  const status=c.enabled&&c.verified?'ON · READ ONLY':c.verified?'VERIFIED · OFF':'NOT VERIFIED · OFF';
  const actions=c.verified?(c.enabled?btn('STOP READING','cloud-source-off:'+c.chat_id,'btn-muted'):btn('ENABLE READ-ONLY','cloud-source-on:'+c.chat_id,'btn-primary')):
   (cloud.telegramBotReady?btn('VERIFY ADMIN ACCESS','cloud-challenge:'+c.chat_id,'btn-muted'):'<span class="text-note">Waiting for Bot configuration</span>');
  return `<div class="connection-source"><div><b>${esc(c.label)}</b> <span class="connection-status ${c.enabled?'linked':'pending'}">${status}</span>
   <div class="text-note">Chat ID ${esc(c.chat_id)} · ${esc(c.kind)} · Last received: ${c.last_observed_at?esc(slt(new Date(c.last_observed_at))):'never'}</div>
   <div class="option-list">${actions}</div></div></div>`;
 }).join('');
 const proof=lastProof&&lastProof.expires_at>Date.now()?`<div class="pair-token"><b>One-time verification message for Chat ${esc(lastProof.chat_id)}</b>
 <input aria-label="One-time chat proof" readonly value="${esc(lastProof.code)}" onclick="this.select()">
 <p class="text-note">Post this exact message as a Telegram channel/group administrator within 15 minutes. Then tap REFRESH. Do not send the code to strangers.</p></div>`:'';
 return surface('OPTIONAL · TELEGRAM BOT CONNECTION',`
 <div class="info"><b>Bot webhook: ${cloud.telegramBotReady?'CONFIGURED — ADD BOT TO CHAT':'NOT CONFIGURED'}.</b>
 This is opt-in Bot API mode: it does NOT access your personal Telegram account or discover private groups. Messages appear only after a permitted chat adds the Bot, verification succeeds, and the source is enabled. Trading remains OFF.</div>
 <div class="control-group"><b>Step 1 • Authorize the Telegram bot</b><p class="text-note">
 Add the platform's configured EdgeQuant bot to your group/channel with required read privileges (channel: admin).
 In a group, an admin can send <b>/eqid</b> to obtain its numeric chat ID. Channel owners can obtain its ID through a bot-admin setup.
 ${cloud.telegramBotReady?'The Bot webhook can process authorized updates.':'An operator must first configure the Bot token and webhook secret in encrypted Vercel Production settings, and set the Telegram webhook.'}</p></div>
 ${botInfo}
 <div class="control-group"><b>Step 2 • Register your permitted source</b>
 ${cloud.telegramInboxReady?`<div class="form-row"><label class="field">Telegram numeric Chat ID<input id="tg-cloud-chat" placeholder="-1001234567890" maxlength="24" autocomplete="off"></label>
 <label class="field wide">Channel / Group label<input id="tg-cloud-label" placeholder="Gold Limit VIP" maxlength="80"></label>
 <label class="field">Signal mode<select id="tg-cloud-kind"><option>LIMIT</option><option>MARKET</option></select></label>
 ${btn('REGISTER SOURCE (OFF)','cloud-add-channel','btn-primary')}</div>`:'<div class="notice">Account-scoped Telegram database is not ready.</div>'}</div>
 <div class="control-group"><b>Step 3 • Verify & enable read-only inbox</b>
 <p class="text-note">Tap VERIFY ADMIN ACCESS for your source, post the one-time code as a chat admin, refresh the page, then enable read-only. Unverified source IDs cannot receive messages.</p>
 <div class="option-list">${btn('REFRESH VERIFIED SOURCES','cloud-refresh','btn-muted')}</div>
 ${proof}
 ${all||empty('No Telegram sources registered yet.')}
 </div>
 <div class="control-group"><b>Alternative: personal Telegram account / MTProto listener</b>
 <p class="text-note">Private chat/group list discovery and Telegram phone OTP need a separate encrypted account listener service. Bot mode does not provide those features.</p>
 <p class="text-note">Account-listener worker request: ${cloud.telegramRequest?.state?esc(cloud.telegramRequest.state):'NOT SUBMITTED'}</p>
 ${cloud.telegramRequestReady?(sources.length?btn('REQUEST ACCOUNT LISTENER','cloud-telegram-listener-request','btn-muted'):'<p class="text-note">Register a source before requesting.</p>'):'<p class="text-note">Request service unavailable.</p>'}</div>
 `, 'Verified user only • Read-only messages • Zero MT5 order actions');
}
function readOnlyGoldPreview(p){
 if(!p||p.status!=='PARSED_PREVIEW'||!Array.isArray(p.entries))return '';
 const plans=p.entries.map(e=>'<div class="text-note mono">Entry '+esc(e.source_entry)+' · L1 TP '+esc(e.layer1?.tp)+' · L2 TP '+esc(e.layer2?.tp)+' · SL '+esc(e.layer1?.sl)+'</div>').join('');
 return '<div class="notice"><b>READ-ONLY SIGNAL PREVIEW · '+esc(p.direction)+' '+esc(p.symbol)+' (NOT SENT)</b>'+plans+'<small class="muted">STOP/LIMIT route awaits a verified MT5 worker quote. No orders placed.</small></div>';
}
function channels(){
 const messages=Array.isArray(cloud.inbox)?cloud.inbox:[];
 const rows=messages.slice(0,15).map(m=>`<div class="activity-item"><div><b>${esc(m.kind)} · Chat ${esc(m.chat_id)}</b>
 <p class="text-note" style="white-space:pre-wrap">${esc(m.body).slice(0,3000)}</p>
 ${readOnlyGoldPreview(m.signal_preview)}
 <small class="muted">${m.observed_at_ms?esc(slt(new Date(Number(m.observed_at_ms)))):'No timestamp'}</small></div></div>`).join('');
 return cloudPersonalTelegram()+surface('RECEIVED TELEGRAM MESSAGES · READ ONLY',rows||empty('No messages received from an enabled Telegram source.'),'Signed private listener or verified Bot webhook • Trading OFF')+cloudTelegram()+note();
}
function channelRows(){if(!prefs.channels.length)return empty('No channels configured in this browser demo. Add a draft label above.');return `<div class="table-scroll"><table class="data-table"><thead><tr><th>CHANNEL</th><th>TYPE</th><th>ACTIVE</th><th>SIGNALS TODAY</th><th>MANAGE</th></tr></thead><tbody>${prefs.channels.map((c,i)=>`<tr><td>${esc(c.name)}</td><td>${esc(c.kind)}</td><td><button data-action="channel-toggle:${i}" class="btn btn-xs ${c.enabled?'btn-outline':'btn-muted'}">${c.enabled?'ON • DRAFT':'OFF • DRAFT'}</button></td><td>—</td><td><button class="btn btn-xs btn-muted" data-action="channel-remove:${i}">REMOVE</button></td></tr>`).join('')}</tbody></table></div>`}
function brokers(){return surface('MT5 CLOUD CONNECTION STATUS',
 '<div class="info"><b>DEMO READ-ONLY STAGE.</b> Register your MT5 DEMO account details below. This does not log into MetaTrader or place orders. A dedicated signed Windows worker must be assigned before the connection becomes active.</div><div class="control-group"><b>Step 1 • Save DEMO account metadata</b><p class="text-note">Enter broker, server and account number. Your password is never requested in this page.</p></div>')+
 cloudBrokerRegistration()+
 surface('Step 2 • Request isolated MT5 worker',
 '<p class="text-note">After saving the DEMO account, tap REQUEST DEMO CLOUD WORKER on its account card. The request is stored privately, but an operator must provision the worker; it does not turn on trading.</p>'+realBrokerSummary(),
 'Verified, account-scoped broker status')+
 note()}
function brokerRows(){if(!prefs.brokers.length)return empty('No broker workers attached. Add a display label above to preview broker cards.');return `<div class="row-grid" style="margin:12px 0">${prefs.brokers.map((b,i)=>`<div class="control-group"><div class="split"><b>${esc(b.label)}</b><span class="status-pill">OFFLINE</span></div><div class="mt5-detail">Server: ${esc(b.server||'—')}<br>Balance: — | Equity: —<br>Floating P&L: — | Spread: —<br>Worker: not provisioned</div><button class="btn btn-xs btn-muted" data-action="broker-remove:${i}">REMOVE DRAFT</button></div>`).join('')}</div>`}
function journal(){return note()+surface('TRADE JOURNAL / FULL HISTORY',`${sectionHeading('CHANNEL VS MT5 • REALIZED / FLOATING / PENDING')}${tabs(['All','Open','Pending','Closed','Cancelled'])}<div class="option-list">${btn('REFRESH','offline-info')}${btn('SAVE AS PDF','offline-info','btn-muted')}${btn('OPEN IN EXCEL','offline-info','btn-muted')}</div><div class="table-scroll"><table class="data-table"><thead><tr><th>SLT TIME</th><th>CHANNEL</th><th>BROKER</th><th>SYMBOL</th><th>TYPE</th><th>ENTRY</th><th>SL</th><th>TP</th><th>REALIZED P&L</th><th>STATUS</th></tr></thead></table></div>${empty('No journal entries. Actual broker tickets and executed trades are not available in UI demo.')}`)}
function tabs(items){return `<div class="tabs" style="margin:10px 0">${items.map(t=>`<button class="tab ${filter===t.toLowerCase()?'active':''}" data-filter="${esc(t.toLowerCase())}">${t}</button>`).join('')}</div>`}
function progress(){return note()+surface('CHANNEL PROGRESS / REALIZED RESULTS',`${sectionHeading('SOURCE PERFORMANCE / RANKING')}${tabs(['Today','Week','Month','All'])}<div class="row-grid">${metric('SIGNALS','—')}${metric('TRIGGERED','—','mint')}${metric('REALIZED NET P&L','—','purple')}</div>${empty('No connected Telegram channels or journal results. Rankings count realized P&L only, not floating P&L.')} ${btn('TRADE JOURNAL','nav:journal')}`)}
function manual(){return note()+surface('MANUAL TRADES / EXTERNAL POSITIONS',`${sectionHeading('NON-EDGEQUANT MT5 TRADES','Live MT5 terminal required')}${empty('No MT5 terminal connected. External trades cannot be viewed or edited here.')}<div class="option-list">${btn('REFRESH MT5 SNAPSHOT','offline-info')}${btn('EDIT SELECTED TRADE','offline-info','btn-muted')}</div><div class="text-note">Desktop manual trade edit requires explicit preview and confirmation. Cloud manual order editing is not connected.</div>`)}
function calendar(){const y=calDate.getFullYear(),m=calDate.getMonth(),first=new Date(y,m,1).getDay(),offset=(first+6)%7,count=new Date(y,m+1,0).getDate(),today=new Date();return note()+surface('PROFIT CALENDAR / REALIZED P&L',`${sectionHeading('MONTHLY PERFORMANCE','No MT5 journal data connected')}<div class="split"><div class="panel-title">${calDate.toLocaleDateString('en-GB',{month:'long',year:'numeric'})}</div><div class="option-list">${btn('‹ PREV','calendar-prev','btn-muted')}${btn('THIS MONTH','calendar-now','btn-muted')}${btn('NEXT ›','calendar-next','btn-muted')}</div></div><div class="calendar-grid">${['MON','TUE','WED','THU','FRI','SAT','SUN'].map(x=>`<div class="cal-head">${x}</div>`).join('')}${Array.from({length:offset},()=>'<div class="cal-day empty-day"></div>').join('')}${Array.from({length:count},(_,i)=>{const day=i+1;return `<button class="cal-day ${day===today.getDate()&&m===today.getMonth()&&y===today.getFullYear()?'today':''} ${selectedDate===`${y}-${m}-${day}`?'selected':''}" data-action="calendar-day:${day}">${day}<div class="text-note" style="margin-top:10px;font-size:9px">—</div></button>`}).join('')}</div><p class="text-note">Daily realized amounts are intentionally blank until a real trade journal is connected.</p>`)}
function plan(){return note()+surface('TRADING PLAN / DAILY TARGET',`${sectionHeading('DAILY RISK POLICY')}${check('ENABLE DAILY TARGET','targetEnabled')} ${check('ENABLE LOSS LIMIT','lossEnabled')}<div class="form-row">${field('TARGET USD','dailyTarget','number','min="0"')}${field('LOSS LIMIT USD','dailyLoss','number','min="0"')}${field('MAX OPEN TRADES','maxTrades','number','min="1" max="100"')}${btn('SAVE PLAN DRAFT','draft-save','btn-primary')}</div><div class="control-group"><div class="split"><b>Daily target progress</b><span class="status-pill">NOT CONNECTED</span></div><div class="progress-bar"><div style="width:0%"></div></div><div class="text-note">Target/loss limits will block new signals only after a secure, verified engine is connected. These draft controls do not enforce risk.</div></div><div class="option-list">${btn('EXPORT PLAN PDF','offline-info','btn-muted')}${btn('EXPORT EDITABLE PLAN','offline-info','btn-muted')}</div>`)}
function profile(){
 const logged=cloud.authenticated?`<div class="info">Signed in: ${esc(cloud.user?.email)} · ${esc(cloud.user?.role)} · Read-only. No trading.</div>${btn('SIGN OUT CLOUD SESSION','cloud-logout','btn-muted')}`:'';
 const login=cloud.database&&!cloud.authenticated?`<h3>SIGN IN</h3><p class="text-note">Use your verified EdgeQuant email, account password and the 6-digit authenticator code.</p><div class="form-row"><label class="field wide">Verified Email<input id="cloud-login-email" type="email" autocomplete="username" maxlength="254"></label><label class="field wide">Account Password (not MT5)<input id="cloud-login-password" type="password" autocomplete="current-password"></label><label class="field">Authenticator code<input id="cloud-login-code" inputmode="numeric" maxlength="6" autocomplete="one-time-code"></label>${btn('SIGN IN (READ-ONLY)','cloud-login','btn-primary')}</div><p class="text-note"><a href="/forgot-password.html">Forgot your password? Reset securely by email</a></p>`:'';
 const signup=cloud.registration&&!cloud.authenticated?`<h3>CREATE SECURE ACCOUNT</h3><p class="text-note">Test registration is limited to the configured test email. Choose Receiver or Provider once; the role cannot be changed after registration.</p><div class="form-row"><label class="field wide">Email<input id="cloud-signup-email" type="email" autocomplete="email" maxlength="254"></label><label class="field wide">Account password (12+ chars, letter + number)<input id="cloud-signup-password" type="password" autocomplete="new-password" minlength="12"></label><label class="field">Lock account role<select id="cloud-signup-role"><option value="receiver">Receiver</option><option value="provider">Provider</option></select></label>${btn('REGISTER + VERIFY EMAIL','cloud-signup','btn-primary')}${btn('RESEND VERIFICATION','cloud-resend','btn-muted')}</div><div class="info">Verification link will arrive by email. Finish authenticator setup before sign-in. No MT5 passwords accepted.</div>`:'';
  const authChoice=!cloud.authenticated?`<div class="auth-choice" role="tablist" aria-label="Cloud account actions"><button type="button" role="tab" aria-selected="${authTab==='login'}" class="${authTab==='login'?'active':''}" data-action="auth-tab:login">SIGN IN</button><button type="button" role="tab" aria-selected="${authTab==='register'}" class="${authTab==='register'?'active':''}" data-action="auth-tab:register">REGISTER</button></div>`:'';
  const unavailableSignup='<div class="info">Registration is currently unavailable. Check cloud health and email settings. Existing verified accounts can still sign in.</div>';
  const content=cloud.database?(cloud.authenticated?logged:authChoice+(authTab==='login'?login:(signup||unavailableSignup))):empty('Secure account service is temporarily unavailable. No account passwords are accepted while offline.');
 return cloud.authenticated?surface('ACCOUNT PROFILE',`${content}<div class="info">Email and account role are verified server-side. Your role cannot be changed from local browser settings.</div>`,'Account identity • Read-only cloud mode'):surface('WELCOME TO EDGEQUANT',`${content}<p class="text-note">Secure email + password + authenticator login. Trading is disabled while cloud integrations are being developed.</p>`,'Sign in or register to access the dashboard')
}
function studio(){return note()+surface('SIGNAL PROVIDER STUDIO',`${sectionHeading('COMPOSE / PREVIEW / PUBLISH','Preview only — no Telegram posting')}<div class="form-row"><label class="field wide"><span>SYMBOL</span><select id="sig-symbol"><option>XAUUSD</option><option>EURUSD</option><option>AUDUSD</option><option>USDCAD</option></select></label><label class="field"><span>DIRECTION</span><select id="sig-side"><option>BUY</option><option>SELL</option></select></label><label class="field"><span>ORDER TYPE</span><select id="sig-kind"><option>BUY/SELL LIMIT</option><option>MARKET</option><option>STOP</option></select></label></div><div class="form-row"><label class="field"><span>ENTRY</span><input id="sig-entry" type="number" step="0.01" placeholder="e.g. 3998"></label><label class="field"><span>RANGE END</span><input id="sig-range" type="number" step="0.01" placeholder="optional"></label><label class="field"><span>STOP LOSS</span><input id="sig-sl" type="number" step="0.01" placeholder="optional"></label><label class="field"><span>TAKE PROFIT</span><input id="sig-tp" type="number" step="0.01" placeholder="optional"></label><label class="field"><span>TP1 QUICK PIPS</span><input id="sig-quick" type="number" min="1" value="${prefs.tp1}"></label></div><div class="option-list">${btn('VALIDATE / PREVIEW','compose-signal','btn-primary')}${btn('SEND WITH LOGO','offline-info','btn-muted')}<span class="status-pill">PUBLISHING DISABLED</span></div><div id="studio-result" class="result-pad">Fill in signal parameters and tap VALIDATE / PREVIEW. Preview text stays on this device.</div>`)+surface('PROVIDER DESTINATION DIRECTORY',`${sectionHeading('TELEGRAM GROUPS / CHANNELS')}${empty('Provider Telegram account is not connected. Group creation, invite links, publishing, follower payments and reporting are not available.')}`)}
function advanced(){return note()+surface('ADVANCED / SIGNAL ENGINE SETTINGS',`${sectionHeading('STRATEGY / RISK / TRADING HOURS')}${controlsProtection()}<div class="form-row">${field('TP1 PIPS','tp1','number','min="1"')}${field('MAX OPEN TRADES','maxTrades','number','min="1"')}${field('MAX SPREAD (PIPS)','spreadMax','number','min="0" step="0.1"')}${btn('SAVE ADVANCED DRAFT','draft-save')}</div><div class="option-list">${check('TELEGRAM UPDATE NOTIFICATIONS','telegramAlert')} ${check('AGENT ENABLED (UI DRAFT)','agent')}</div><div class="notice">Setting Agent ON here does not start trading or permit orders. The real engine remains off and is not installed in this public web app.</div>`)}
function preview(){return note()+surface('SIGNAL PREVIEW / FORMAT ANALYZER',`${sectionHeading('PARSE AN INCOMING TELEGRAM MESSAGE','Simplified UI demo parser, NOT Windows engine parser')}<textarea id="source-text" placeholder="GOLD SELL 3998-3996-3994 SL 4003 TP 3970"></textarea><div class="option-list" style="margin-top:10px">${btn('LOAD AN EXAMPLE','example-signal')}${btn('ANALYZE','analyze-signal','btn-primary')}${btn('CLEAR','clear-signal','btn-muted')}</div><div id="parse-result" class="result-pad" style="margin-top:11px">No message analyzed. This demo does not place trades.</div>`)}
function activity(){return note()+surface('ACTIVITY / ENGINE DIAGNOSTICS',`${sectionHeading('LOCAL BROWSER EVENTS','Sri Lankan time • No MT5 worker telemetry')}<div class="activity-list">${log.slice().reverse().map(l=>`<div class="activity-item"><div class="activity-dot">●</div><div><b>${esc(l.title)}</b><div class="text-note">${esc(l.detail)}</div><small class="muted mono">${slt(l.date)}</small></div></div>`).join('')}</div>`)}
function settings(){return note()+surface('SETTINGS / APP PREFERENCES',`${sectionHeading('DISPLAY, LANGUAGE & ALERTS')}${select('PREFERRED LANGUAGE','language',[['EN','English'],['SI','සිංහල']])} ${select('VOICE','voice',[['SI','Sinhala'],['EN','English'],['OFF','Off']])} ${select('THEME','theme',[['neon','Neon Dark'],['blue','Midnight Blue']])}<div class="option-list" style="margin-top:13px">${check('TELEGRAM REPORTS (DRAFT)','telegramAlert')}${check('AGENT ON (DRAFT; NO ORDERS)','agent')}</div><div class="option-list" style="margin-top:12px">${btn('SAVE SETTINGS','draft-save','btn-primary')}${btn('RESET LOCAL DEMO SETTINGS','reset-demo','btn-muted')}</div><p class="text-note">Preferences are saved in localStorage on this browser only. No passwords, OTP, MT5 login or Telegram tokens are stored.</p>`)}
function guide(){return surface('GUIDE / UPADES',`${sectionHeading('RECEIVER & PROVIDER QUICK GUIDE')}<div class="control-group"><b class="cyan">Signal Receiver</b><p class="text-note">Select Receiver, confirm email and configure broker, Telegram subscriptions and risk controls when secure cloud backend is available. No such account can be created in this demo.</p></div><div class="control-group"><b class="cyan">Signal Provider</b><p class="text-note">Select Provider to access Signal Studio. Publishing to Telegram, managing followers, subscriptions and broker integrations require verified cloud services.</p></div><div class="control-group"><b class="amber">Important safety</b><p class="text-note">Real brokers need separate cloud Windows MT5 workers, account isolation, secure credentials, idempotent orders, live DEMO acceptance tests and daily risk limits. Static Vercel pages do not execute trades.</p></div>`)}
function welcome(){const role=cloud.user?.role==='provider'?'Provider':'Receiver';return surface('YOUR VERIFIED ACCOUNT ROLE',
 `<div class="control-group"><b class="cyan">${esc(role.toUpperCase())} ACCOUNT</b><p class="text-note">Your account role was chosen during registration and is locked. It cannot be switched through the browser UI.</p><div class="option-list">${btn('OPEN DASHBOARD','nav:dashboard','btn-primary')}${role==='Provider'?btn('OPEN SIGNAL STUDIO','nav:studio','btn-muted'):btn('SET UP TELEGRAM','nav:channels','btn-muted')}${btn('SET UP MT5','nav:brokers','btn-muted')}</div></div>`,'Separate Receiver and Provider workspaces • Trading OFF');
}
const renderers={dashboard,channels,brokers,journal,progress,manual,calendar,plan,profile,studio,advanced,preview,activity,settings,guide,welcome};
function nav(p){if(!renderers[p])return;if(!cloud.authChecked||!cloud.authenticated){p='profile';}else if(p==='studio'&&cloud.user?.role!=='provider'){message('Signal Studio is available to Provider accounts only.');return;}page=p;filter='all';render();closeSidebar();window.scrollTo({top:0,behavior:'instant'})}
function renderNav(){const txt=prefs.language==='SI'?'si':'en';$('#sidebar-nav').innerHTML=GROUPS.map(g=>`<div class="nav-group"><div class="nav-group-title">${g.title}</div>${g.items.filter(i=>i[0]!=='studio'||cloud.user?.role==='provider').map(i=>`<button class="nav-item ${page===i[0]?'active':''}" type="button" data-page="${i[0]}"><span class="nav-dot">◆</span><span>${txt==='si'?i[2]:i[1]}</span></button>`).join('')}</div>`).join('');const mobiles=[['dashboard','▦','Home'],['channels','♧','Channels'],['brokers','▥','Brokers'],['journal','▤','Trades'],['more','☰','More']];$('#mobile-nav').innerHTML=mobiles.map(([id,icon,label])=>`<button class="${page===id?'active':''}" type="button" data-page="${id}"><span class="icon">${icon}</span><span>${label}</span></button>`).join('')}
function render(){
 const signedIn=cloud.authChecked&&cloud.authenticated;
 const activePage=signedIn?page:'profile';
 document.body.classList.toggle('auth-gated',!signedIn);
 if(!signedIn)closeSidebar();
 const item=GROUPS.flatMap(g=>g.items).find(x=>x[0]===activePage);
 $('#page-title').textContent=!cloud.authChecked?'Checking secure session…':!signedIn?'Sign in to EdgeQuant':prefs.language==='SI'?(item?.[2]||'Dashboard'):(item?.[1]||'Dashboard');
 $('#page-subtitle').textContent=!signedIn?'Email-verified account access • Receiver or Provider':SUBTITLE[activePage]||'';
 $('#page-content').innerHTML=!cloud.authChecked?'<section class="surface auth-wait">Checking your secure cloud session…</section>':renderers[activePage]();
 $('#page-state').textContent=simulation?'TEST MODE':'STOPPED';
 $('.mode-value').textContent=simulation?'test only':'stopped';
 $('#lang-picker').value=prefs.language;$('#theme-picker').value=prefs.theme;$('#voice-picker').value=prefs.voice;
 document.body.classList.toggle('blue-theme',prefs.theme==='blue');
 if(signedIn)renderNav();else{$('#sidebar-nav').innerHTML='';$('#mobile-nav').innerHTML=''}
 updateClock();
 const e=$('#api-health');if(e)e.textContent=!cloud.reachable?'CHECKING / OFFLINE':!cloud.database?'API ONLINE · DB OFF':!cloud.authenticated?'LOGIN REQUIRED':'READ-ONLY ONLINE';
 const accountButton=document.querySelector('.system-strip [data-page="profile"]');if(accountButton)accountButton.textContent=signedIn?'MY ACCOUNT':'LOGIN / REGISTER';
}
function updateClock(){const x=$('#slt-clock');if(x)x.textContent='SRI LANKA • '+slt().split(' SLT')[0]+' SLT'}
function message(s){const el=$('#toast');el.textContent=s;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3200)}
function logEvent(t,d){log.push({date:new Date(),title:t,detail:d});if(log.length>60)log.shift()}
function closeSidebar(){$('#sidebar').classList.remove('open');$('#side-backdrop').classList.remove('show')}
function updatePref(el){const k=el.dataset.pref;if(!k||!Object.prototype.hasOwnProperty.call(DEFAULT,k))return;if(k==='role'){message('Role is locked to your verified account.');return}let v=el.type==='checkbox'?el.checked:el.value;if(el.type==='number'){v=Number(v);if(!Number.isFinite(v)||v<0){message('Invalid number; draft not saved.');return}}if(k==='layers')v=Math.max(1,Math.min(8,Math.floor(v)));if(k==='lot')v=Math.max(.01,v);if(k==='partialPercent')v=Math.max(1,Math.min(99,v));if(k==='maxTrades')v=Math.max(1,Math.floor(v));prefs[k]=v;save();if(['language','theme','voice','role'].includes(k)){render();} }
function act(id){if(!cloud.authenticated&&!['auth-tab:login','auth-tab:register','cloud-resend','cloud-signup','cloud-login'].includes(id)){message('Sign in to EdgeQuant first.');return}if(id==='auth-tab:login'||id==='auth-tab:register'){authTab=id.slice('auth-tab:'.length);render();return}if(id==='cloud-resend'){cloudResendVerification();return}if(id==='cloud-signup'){cloudSignup();return}if(id==='cloud-add-channel'){cloudAddChannel();return}if(id==='cloud-refresh'){checkCloud();return}if(id==='cloud-personal-disconnect'){cloudDisconnectPersonal();return}if(id.startsWith('cloud-personal-on:')){cloudTogglePersonalDialog(id.slice(18),true);return}if(id.startsWith('cloud-personal-off:')){cloudTogglePersonalDialog(id.slice(19),false);return}if(id==='cloud-bot-info'){cloudCheckTelegramBot(false);return}if(id==='cloud-bot-setup'){cloudCheckTelegramBot(true);return}if(id.startsWith('cloud-challenge:')){cloudChannelChallenge(id.slice(16));return}if(id.startsWith('cloud-source-on:')){cloudToggleChannel(id.slice(16),true);return}if(id.startsWith('cloud-source-off:')){cloudToggleChannel(id.slice(17),false);return}if(id.startsWith('cloud-pair-start:')){cloudPairStart(id.slice(17));return}if(id.startsWith('cloud-pair-status:')){cloudPairStatus(id.slice(18));return}if(id.startsWith('cloud-pair-approve:')){cloudPairApprove(id.slice(19));return}if(id==='cloud-telegram-listener-request'){cloudRequestTelegramListener();return}if(id.startsWith('cloud-worker-request:')){cloudRequestWorker(id.slice('cloud-worker-request:'.length));return}if(id==='cloud-login'){cloudLogin();return}if(id==='cloud-broker-register'){cloudRegisterBroker();return}if(id==='cloud-logout'){cloudLogout();return}if(id.startsWith('nav:'))return nav(id.slice(4));if(id==='draft-save'){save();logEvent('Draft settings saved','Saved in this browser only. No engine or cloud worker was modified.');message('Saved on this browser only — no live trading changes.');return}if(id==='offline-info'){message('Unavailable: live cloud MT5 / Telegram backend not connected.');return}if(id==='test-run'){simulation=true;logEvent('UI Test Mode enabled','This changes the page label only. No MT5 orders or account data.');render();message('UI TEST MODE only — no trades sent.');return}if(id==='stop-test'){simulation=false;logEvent('UI Test Mode stopped','No MT5 execution engine was running.');render();message('UI demo test stopped.');return}if(id.startsWith('role:')){message('Account role is locked at registration and cannot be switched.');return}if(id==='add-channel'){const el=$('#new-channel'),name=el?.value?.trim();if(!name)return message('Enter a channel display label.');if(prefs.channels.length>=30)return message('Maximum 30 draft channels.');prefs.channels.push({name:name.slice(0,55),kind:$('#new-channel-kind').value,enabled:false});save();render();message('Channel draft added. Not connected to Telegram.');return}if(id.startsWith('channel-remove:')||id.startsWith('channel-toggle:')){const [,i]=id.split(':'),idx=Number(i);if(!(idx>=0&&idx<prefs.channels.length))return;if(id.startsWith('channel-remove'))prefs.channels.splice(idx,1);else prefs.channels[idx].enabled=!prefs.channels[idx].enabled;save();render();return}if(id==='channels-on'||id==='channels-off'){prefs.channels.forEach(x=>x.enabled=id==='channels-on');save();render();message('Draft channel switches changed only in this browser.');return}if(id==='add-broker'){const label=$('#broker-name')?.value.trim(),server=$('#broker-server')?.value.trim();if(!label)return message('Enter a demo broker label.');if(prefs.brokers.length>=12)return message('Maximum 12 demo broker cards.');prefs.brokers.push({label:label.slice(0,50),server:(server||'').slice(0,70)});save();render();message('Demo broker label added. No MT5 connection.');return}if(id.startsWith('broker-remove:')){const i=Number(id.split(':')[1]);if(i>=0&&i<prefs.brokers.length){prefs.brokers.splice(i,1);save();render()}return}if(id.startsWith('calendar-')){if(id==='calendar-prev')calDate=new Date(calDate.getFullYear(),calDate.getMonth()-1,1);if(id==='calendar-next')calDate=new Date(calDate.getFullYear(),calDate.getMonth()+1,1);if(id==='calendar-now')calDate=new Date();if(id.startsWith('calendar-day:')){selectedDate=`${calDate.getFullYear()}-${calDate.getMonth()}-${id.split(':')[1]}`;message('No realized P&L records available for this date.')}render();return}if(id==='example-signal'){$('#source-text').value='GOLD SELL 3998-3996-3994 SL 4003 TP 3970';return}if(id==='clear-signal'){$('#source-text').value='';$('#parse-result').textContent='No message analyzed. No trades sent.';return}if(id==='analyze-signal'){const s=$('#source-text').value.trim();const m=s.match(/\b(BUY|SELL)\b/i),sym=s.match(/\b(XAUUSD|GOLD|EURUSD|AUDUSD|USDCAD)\b/i),prices=s.match(/\b(?:BUY|SELL)\b[^\d]{0,10}([\d.]+(?:\s*[-–]\s*[\d.]+)*)/i);$('#parse-result').textContent=s?(m&&sym&&prices?`SIMPLE UI PREVIEW ONLY\nDirection: ${m[1].toUpperCase()}\nSymbol: ${sym[1].toUpperCase()==='GOLD'?'XAUUSD':sym[1].toUpperCase()}\nSource entry: ${prices[1]}\nSL: ${s.match(/\bSL\s*:?\s*([\d.]+)/i)?.[1]||'not provided'}\nTP: ${s.match(/\bTP\s*:?\s*([\d.]+)/i)?.[1]||'not provided'}\n\nNO LIVE EXECUTION. Desktop parser rules are not connected.`:'No complete BUY/SELL + symbol + entry detected by this simplified demo. NO trade sent.'):'Paste a sample message first.';return}if(id==='compose-signal'){const sym=$('#sig-symbol').value,side=$('#sig-side').value,entry=$('#sig-entry').value,sl=$('#sig-sl').value,tp=$('#sig-tp').value,rng=$('#sig-range').value;if(!entry||!Number.isFinite(Number(entry))||Number(entry)<=0){message('Enter a valid entry price.');return}$('#studio-result').textContent=`PROVIDER SIGNAL PREVIEW — NOT SENT\n${sym} ${side} ${entry}${rng?' - '+rng:''}\nSL ${sl||'[not set]'} • TP ${tp||'[not set]'}\nQuick layer: +${$('#sig-quick').value||prefs.tp1} pips\nOrder mode: ${$('#sig-kind').value}\n\nTelegram and cloud publishing are disabled.`;return}if(id==='reset-demo'){if(!confirm('Delete this browser\'s UI draft settings and channel/broker labels?'))return;localStorage.removeItem(LS_KEY);window.location.reload()}}
document.addEventListener('click',e=>{const n=e.target.closest('[data-page]');if(n){if(n.dataset.page==='more'){$('#sidebar').classList.add('open');$('#side-backdrop').classList.add('show')}else nav(n.dataset.page);return}const b=e.target.closest('[data-action]');if(b){act(b.dataset.action);return}});
document.addEventListener('change',e=>{const t=e.target;if(t.matches('[data-pref]'))updatePref(t);if(t.id==='lang-picker'){prefs.language=t.value;save();render()}if(t.id==='theme-picker'){prefs.theme=t.value;save();render()}if(t.id==='voice-picker'){prefs.voice=t.value;save();render()}});
document.addEventListener('click',e=>{if(e.target?.id==='mobile-menu-button'){$('#sidebar').classList.add('open');$('#side-backdrop').classList.add('show')}if(e.target?.id==='side-backdrop')closeSidebar();if(e.target.closest('[data-filter]')){filter=e.target.closest('[data-filter]').dataset.filter;render()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeSidebar()});
render();checkCloud();setInterval(updateClock,1000*30);setInterval(checkCloud,30000);
