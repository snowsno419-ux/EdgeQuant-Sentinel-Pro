'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const R=require('../mobile-web/risk-hub');
const app=fs.readFileSync(path.join(__dirname,'../mobile-web/app.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'../mobile-web/styles.css'),'utf8');
test('risk bars never invent daily P&L from floating only',()=>{
 const r=R.calculate({status:'CONNECTED',floating:-40},{lossEnabled:true,lossLimit:100});
 assert.equal(r.dataReady,false);
 assert.equal(r.lossPercent,null);assert.equal(r.lossUsed,null);
 assert.equal(r.floatingExposurePercent,40);assert.equal(r.enforcement,'NOT_CONNECTED_WEB_READ_ONLY');
});
test('separate accounts have independently computed percentages and limits',()=>{
 const a=R.calculate({status:'CONNECTED',today_trading_net:-40,floating:-30},{lossEnabled:true,lossLimit:100});
 const b=R.calculate({status:'CONNECTED',today_trading_net:-15,floating:0},{lossEnabled:true,lossLimit:200});
 assert.equal(a.lossPercent,70);assert.equal(a.remaining,30);
 assert.equal(a.status,'CAUTION');
 assert.equal(b.lossPercent,7.5);assert.equal(b.remaining,185);
 assert.equal(b.status,'SAFE');
});
test('loss breach, target and unusable inputs are handled without false safety',()=>{
 const r=R.calculate({status:'CONNECTED',today_trading_net:-130,floating:-5},
                    {lossEnabled:true,lossLimit:100,targetEnabled:true,targetLimit:50});
 assert.equal(r.lossHit,true);assert.equal(r.lossPercent,100);assert.equal(r.targetPercent,0);
 const t=R.calculate({status:'CONNECTED',today_trading_net:75,floating:0},
                     {lossEnabled:false,targetEnabled:true,targetLimit:60});
 assert.equal(t.targetHit,true);assert.equal(t.targetPercent,100);
 assert.equal(R.calculate({status:'OFFLINE',today_trading_net:100,floating:0},
                  {lossEnabled:true,lossLimit:100}).lossPercent,null);
 assert.equal(R.calculate({status:'CONNECTED',today_trading_net:0,floating:0},
                  {lossEnabled:true,lossLimit:NaN}).lossPercent,null);
});
test('UI shows verified broker cards on Dashboard and Brokers only, web actions are explicitly drafts',()=>{
 assert.match(app,/function riskHubCards\(\)/);
 assert.match(app,/function dashboard\(\)\{return.*riskHubCards\(\)/);
 assert.match(app,/function brokers\(\)\{return riskHubCards\(\)/);
 assert.match(app,/Cloud trading remains OFF/);
 assert.match(app,/localStorage\.setItem\(riskDraftStoreKey\(\)/);
 assert.match(app,/NOT enabled in this web preview/);
 assert.match(css,/\.risk-hub-grid\{/);
 assert.match(css,/@media \(max-width:760px\)/);
});
