'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const app=fs.readFileSync(path.join(__dirname,'../mobile-web/app.js'),'utf8');
function element(){const classes=new Set();return {classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),toggle:(x,on)=>on?classes.add(x):classes.delete(x),contains:x=>classes.has(x)},innerHTML:'',textContent:'',value:'',style:{}}}
async function boot(authenticated){
 const nodes=new Map(),querySelector=k=>{if(!nodes.has(k))nodes.set(k,element());return nodes.get(k)};
 const document={body:element(),querySelector,addEventListener:()=>{}};
 const localStorage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};
 const fetch=async url=>{
  if(url==='/api/health')return {ok:true,json:async()=>({ok:true,database_ready:true,registration_enabled:true,telegram_inbox_ready:true,telegram_listener_request_ready:true,worker_request_ready:true,telegram_connected:false,mt5_worker_connected:false})};
  if(url==='/api/me')return {ok:authenticated,json:async()=>({email:'owner@example.com',role:'receiver'})};
  if(url==='/api/channels')return {ok:true,json:async()=>({channels:[]})};
  if(url==='/api/telegram-inbox')return {ok:true,json:async()=>({messages:[]})};
  if(url==='/api/telegram-listener-requests')return {ok:true,json:async()=>({request:null})};
  if(url==='/api/dashboard')return {ok:true,json:async()=>({brokers:[],telegram_connected:false})};
  throw new Error('Unexpected request: '+url)
 };
 const context=vm.createContext({document,localStorage,window:{scrollTo:()=>{}},fetch,setInterval:()=>0,setTimeout:()=>0,clearTimeout:()=>{},confirm:()=>false});
 vm.runInContext(app+'\nthis.__test={checkCloud,nav,cloud,render,getPage:()=>page}',context);
 await context.__test.checkCloud();
 return {document,nodes,context};
}
test('unauthenticated visitors see login first and no dashboard controls',async()=>{
 const x=await boot(false),page=x.document.querySelector('#page-content').innerHTML;
 assert.equal(x.context.__test.getPage(),'profile');
 assert.equal(x.document.body.classList.contains('auth-gated'),true);
 assert.match(page,/SIGN IN/);
 assert.doesNotMatch(page,/SET UP TELEGRAM|SET UP MT5|LIVE TRADES & PENDING ORDERS/);
 x.context.__test.nav('dashboard');
 assert.equal(x.context.__test.getPage(),'profile');
});
test('authenticated user enters dashboard with honest connection setup',async()=>{
 const x=await boot(true),page=x.document.querySelector('#page-content').innerHTML;
 assert.equal(x.context.__test.getPage(),'dashboard');
 assert.equal(x.document.body.classList.contains('auth-gated'),false);
 assert.match(page,/SET UP TELEGRAM/);
 assert.match(page,/SET UP MT5/);
 assert.match(page,/NOT CONNECTED/);
 assert.doesNotMatch(page,/MT5.*LIVE EXECUTION ON/);
 x.context.__test.nav('channels');
 assert.match(x.document.querySelector('#page-content').innerHTML,/REGISTER SOURCE \(OFF\)/);
 assert.equal(x.document.querySelector('#sidebar-nav').innerHTML.includes('Signal Studio'),false);
});
