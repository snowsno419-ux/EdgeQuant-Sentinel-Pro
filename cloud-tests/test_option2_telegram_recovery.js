'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const R=require('../mobile-web/recovery-preview');
const app=fs.readFileSync(path.resolve(__dirname,'../mobile-web/app.js'),'utf8');
test('recovery uses user supplied reference and does not invent history',()=>{
 assert.equal(R.preview(950,1000,.25).status,'SIMULATED_RECOVERY');
 assert.equal(R.preview(950,1000,.25).recoveryNeeded,50);
 assert.equal(R.preview(950,1000,.25).riskBudget,2.375);
 assert.equal(R.preview(970,1000,.25).status,'SIMULATED_RECOVERY');
 assert.equal(R.preview(971,1000,.25).status,'STANDBY');
});
test('invalid/missing signed equity prevents a green fictitious recovery',()=>{
 for(const bad of [null,undefined,'',0,-5,NaN])assert.equal(R.preview(bad,1000,.25).status,'UNAVAILABLE');
 for(const bad of [null,0,undefined,-2])assert.equal(R.preview(950,bad,.25).status,'UNAVAILABLE');
 assert.equal(R.preview(950,1000,.8).status,'UNAVAILABLE');
});
test('recovery never activates cloud trade execution or lifts loss gates',()=>{
 const data=R.preview(900,1000,.25);
 assert.equal(data.orderExecution,false);
 assert.match(app,/SAVE PREVIEW/);
 assert.match(app,/no automatic recovery trades/i);
 assert.match(app,/Live trading OFF/);
 assert.match(app,/localStorage\.setItem\(riskDraftStoreKey\(\)/);
});
