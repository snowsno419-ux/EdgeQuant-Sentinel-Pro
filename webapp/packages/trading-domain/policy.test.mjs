import {test} from "node:test";
import {strict as assert} from "node:assert";
import {add,planTelegram,planDirectCopy} from "./index.mjs";
const a={login:"123456",server:"IC-Markets-Demo"},rule={pipSize:"0.1"};
test("exact decimal addition",()=>assert.equal(add("0.1","0.2"),"0.3"));
test("Gold Telegram BUY offset and 2 layers",()=>{
 const p=planTelegram({symbol:"XAUUSD",side:"BUY",entry:"4000",sl:"3950",tp:"4100"},a,rule);
 assert.equal(p.adjustedEntry,"4000.99");assert.equal(p.orders.length,2);
 assert.equal(p.orders[0].tp,"4005.99");assert.equal(p.orders[1].tp,"4100");
 assert.deepEqual(p.orders.map(x=>x.sl),["3950","3950"]);
});
test("Gold Telegram SELL offset",()=>{
 const p=planTelegram({symbol:"XAUUSD",side:"SELL",entry:"4000",sl:"4050",tp:"3900"},a,rule);
 assert.equal(p.adjustedEntry,"3999.1");
});
test("repeated Telegram signal dedupes by identity not message ID",()=>{
 const one=planTelegram({symbol:"XAUUSD",side:"BUY",entry:"4000.00",sl:"3950",tp:"4100",messageId:"A"},a,rule);
 const two=planTelegram({symbol:"xauusd",side:"buy",entry:"4000",sl:"3950.00",tp:"4100",messageId:"B"},a,rule);
 assert.equal(one.duplicateKey,two.duplicateKey);
});
test("Direct MT5 copy is one exact order without Telegram offset",()=>{
 const p=planDirectCopy({orderId:77,type:"BUY_LIMIT",symbol:"XAUUSD",entry:"4000",sl:"3950",tp:"4100"},a,{login:888,server:"Deriv-Demo"});
 assert.equal(p.orders.length,1);assert.equal(p.orders[0].entry,"4000");assert.equal(p.orders[0].tp,"4100");
});
test("invalid account is blocked",()=>assert.throws(()=>planTelegram({symbol:"XAUUSD",side:"BUY",entry:"4000"}, {},rule)));
