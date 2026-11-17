'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {preview}=require('../mobile-web/api/_lib/signal-preview');
test('SELL LIMIT produces exactly two projected layers',()=>{
 const p=preview('GOLD SELL LIMIT 3876.1\nSL 3882\nTP 3860');
 assert.equal(p.status,'PARSED_PREVIEW');
 assert.equal(p.read_only,true);assert.equal(p.executable,false);
 assert.equal(p.entries.length,1);
 assert.deepEqual(p.entries[0].layer1,{entry:3876.1,sl:3882,tp:3871.1});
 assert.deepEqual(p.entries[0].layer2,{entry:3876.1,sl:3882,tp:3860});
});
test('BUY LIMIT L1 takes 50 project Gold pips and L2 signal TP',()=>{
 const p=preview('GOLD BUY LIMIT 3880.2 SL 3872 TP 3895');
 assert.equal(p.status,'PARSED_PREVIEW');
 assert.equal(p.entries[0].layer1.tp,3885.2);
 assert.equal(p.entries[0].layer2.tp,3895);
});
test('two source entries create two separately projected layer pairs',()=>{
 const p=preview('XAUUSD SELL LIMIT 3913-3914 SL 3920 TP 3900');
 assert.equal(p.entries.length,2);
 assert.equal(p.entries[0].layer1.tp,3908);
 assert.equal(p.entries[1].layer1.tp,3909);
 assert.equal(p.entries[1].layer2.tp,3900);
});
test('choose TP3 for second layer when TP1/2/3 exist',()=>{
 const p=preview('GOLD BUY 3880 SL 3870 TP1 3883 TP2 3885 TP3 3892');
 assert.equal(p.status,'PARSED_PREVIEW');
 assert.equal(p.entries[0].layer2.tp,3892);
});
test('management messages, missing SL/TP, wrong-side protections never become orders',()=>{
 for(const body of ['GOLD SELL LIMIT 3876 SL 3870 TP 3860','GOLD BUY LIMIT 3876 SL 3900 TP 3910','GOLD SELL LIMIT 3876 TP 3860','GOLD BUY 3876 SL 3860','GOLD BUY 3876 SL 3860 TP 3900 CLOSE','GOLD BUY SELL 3876 SL 3860 TP 3900','EURUSD BUY 1.1 SL 1.0 TP 1.2']){
  const p=preview(body);assert.equal(p.status,'UNPARSED',body);assert.equal(p.executable,false,body);
 }
});
test('near-market STOP pricing requires verified MT5 worker quote',()=>{
 const p=preview('XAUUSD SELL LIMIT 3876.8 SL 3882 TP 3860');
 assert.equal(p.pending_route,'AWAIT_BROKER_BID_ASK_AND_STOPS_LEVEL');
 assert.equal(p.broker_quote_verified,false);assert.equal(p.executable,false);
 assert.equal('mt5_request' in p,false);
});
test('untrusted input size/shape is bounded',()=>{
 assert.equal(preview(null).status,'UNPARSED');
 assert.equal(preview('x'.repeat(4000)).status,'UNPARSED');
 assert.equal(preview('CANCEL ALL').status,'UNPARSED');
});
