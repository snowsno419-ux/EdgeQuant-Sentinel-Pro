'use strict';
/* Phase 7 — read-only GOLD/XAUUSD two-layer projection. This is NOT an MT5 executor.
   Desktop rule reference: EdgeQuant Sentinel Pro v2.0.4 (2026-11-17). */
const GOLD_PIP=0.1;
const LAYER1_PIPS=50;
const priceToken='(\\d{3,6}(?:\\.\\d{1,3})?)';
const actionWords=/\b(?:CANCEL|CLOSE|CLOSED|HOLD|BOOK|BREAKEVEN|BREAK[ -]?EVEN|MOVE\s+SL|BE\s+NOW|PARTIAL|DON'?T\s+TAKE|DO\s+NOT\s+TAKE)\b/i;
function number(x){const n=Number(x);return Number.isFinite(n)&&n>0&&n<1e7?n:null}
function round(x){return Math.round((x+Number.EPSILON)*1000)/1000}
function failure(reason){return {status:'UNPARSED',reason,read_only:true,executable:false}}
function preview(message){
 if(typeof message!=='string'||message.length>3000)return failure('invalid_message');
 const text=message.replace(/\r/g,' ').trim();
 if(!text)return failure('empty_message');
 if(actionWords.test(text))return failure('management_message_not_new_trade');
 if(!/\b(?:GOLD|XAUUSD(?:[.a-z0-9_-]{0,12})?)\b/i.test(text))return failure('gold_symbol_not_confirmed');
 const ds=[...text.matchAll(/\b(BUY|SELL)\b/gi)];
 if(ds.length!==1)return failure('direction_missing_or_ambiguous');
 const direction=ds[0][1].toUpperCase();
 const rest=text.slice(ds[0].index+ds[0][0].length);
 const orderWord=rest.match(/^\s*(LIMIT|STOP|MARKET)\b/i);
 const originalType=orderWord?orderWord[1].toUpperCase():'LIMIT';
 // Only entry values following the direction qualify as entries; never SL/TP values.
 const lead=rest.replace(/^\s*(?:LIMIT|STOP|MARKET)\b/i,'').replace(/^\s*(?:XAUUSD(?:[.a-z0-9_-]{0,12})?|GOLD)\b/i,'').replace(/^\s*(?:ENTRY|ENTRIES|EP)\s*[:=@-]?/i,'').trim();
 const entryPattern=new RegExp('^[:=@\\s]*'+priceToken+'(?:\\s*[-–]\\s*'+priceToken+')?(?:\\s*[-–]\\s*'+priceToken+')?','i');
 const em=lead.match(entryPattern);
 if(!em)return failure('entry_missing');
 const entryValues=[em[1],em[2],em[3]].filter(Boolean).map(number);
 if(entryValues.some(x=>x===null))return failure('invalid_entry');
 const entries=[...new Set(entryValues)];
 if(!entries.length||entries.length>3)return failure('invalid_entry_count');
 const slm=text.match(new RegExp('\\bSL\\s*[:=@-]?\\s*'+priceToken+'\\b','i'));
 const sl=slm?number(slm[1]):null;
 if(sl===null)return failure('stop_loss_missing');
 const tps=[...text.matchAll(/\bTP([1-3])?\b\s*[:=@-]?\s*(\d{3,6}(?:\.\d{1,3})?)\b/gi)]
  .map(m=>({index:m[1]?Number(m[1]):0,value:number(m[2])}));
 if(!tps.length||tps.some(tp=>tp.value===null))return failure('signal_take_profit_missing');
 const tp2=tps.find(x=>x.index===3)?.value??tps.find(x=>x.index===2)?.value??tps.find(x=>x.index===1)?.value??tps[0].value;
 const results=[];
 for(const entry of entries){
  const tp1=round(entry+(direction==='BUY'?1:-1)*GOLD_PIP*LAYER1_PIPS);
  const good=direction==='BUY'?sl<entry&&tp1>entry&&tp2>entry:sl>entry&&tp1<entry&&tp2<entry;
  if(!good)return failure('sl_or_tp_on_wrong_side');
  results.push({source_entry:entry,layer1:{entry,sl,tp:tp1},layer2:{entry,sl,tp:tp2}});
 }
 return {status:'PARSED_PREVIEW',read_only:true,executable:false,symbol:'XAUUSD',direction,original_order_type:originalType,
  broker_quote_verified:false,pending_route:'AWAIT_BROKER_BID_ASK_AND_STOPS_LEVEL',
  near_market_rule:'Desktop v2.0.4: within 15 Gold pips, prefer broker-valid STOP after verified quote and SL/TP validation',
  pip_size_reference:GOLD_PIP,layers_per_entry:2,entries:results};
}
module.exports={preview};
