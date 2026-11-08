// Pure policy planning ONLY. No MT5 orders or credentials are sent from this module.
const decimal = (v) => {
 const s=String(v).trim();
 if (!/^-?[0-9]+(?:\.[0-9]+)?$/.test(s)) throw Error("invalid decimal: "+s);
 return s;
};
const scale = (s) => (s.split(".")[1]||"").length;
const int = (s,d) => {
 const neg=s[0]==="-"; const n=neg?s.slice(1):s; const parts=n.split(".");
 return (neg?-1n:1n)*(BigInt(parts[0])*10n**BigInt(d)+BigInt((parts[1]||"").padEnd(d,"0")||"0"));
};
const str = (n,d) => {
 const minus=n<0n?"-":""; const x=n<0n?-n:n; const pow=10n**BigInt(d);
 const fractional=(x%pow).toString().padStart(d,"0").replace(/0+$/,"");
 return minus+(x/pow).toString()+(fractional?"."+fractional:"");
};
export function add(...values) {
 const strings=values.map(decimal); const d=Math.max(...strings.map(scale));
 return str(strings.reduce((sum,s)=>sum+int(s,d),0n),d);
}
const norm=(s)=>add(decimal(s),"0");
const scope=(a)=>{ if(!a||!String(a.login||"").trim()||!String(a.server||"").trim())throw Error("account login/server required");return String(a.server).toLowerCase()+":"+String(a.login)};
const sideOf=(s)=>{const v=String(s).toUpperCase();if(v!=="BUY"&&v!=="SELL")throw Error("invalid side");return v};
const mul=(s,n)=>{const x=decimal(s);if(!Number.isSafeInteger(n))throw Error("invalid pip multiplier");return str(int(x,scale(x))*BigInt(n),scale(x))};
export function planTelegram(signal, account, rule) {
 const side=sideOf(signal.side), symbol=String(signal.symbol).trim().toUpperCase();
 if(!symbol)throw Error("symbol required");
 const original=norm(signal.entry);
 const offset=symbol.startsWith("XAUUSD")?(side==="BUY"?(rule.goldBuyOffset??"0.99"):(rule.goldSellOffset??"-0.90")):"0";
 const entry=add(original,offset), sign=side==="BUY"?1:-1;
 const pip=decimal(rule.pipSize), tp1Pips=rule.tp1Pips??50, tp2Pips=rule.tp2FallbackPips??150, slPips=rule.slFallbackPips??50;
 for(const x of [tp1Pips,tp2Pips,slPips])if(!Number.isSafeInteger(x)||x<=0)throw Error("invalid pip config");
 const sl=signal.sl==null||signal.sl===""?add(entry,mul(pip,-sign*slPips)):norm(signal.sl);
 const tp2=signal.tp==null||signal.tp===""?add(entry,mul(pip,sign*tp2Pips)):norm(signal.tp);
 const tp1=add(entry,mul(pip,sign*tp1Pips));
 return {mode:"TELEGRAM",account:scope(account),symbol,side,originalEntry:original,adjustedEntry:entry,
  duplicateKey:JSON.stringify([scope(account),symbol,side,original,sl,tp2]),
  orders:[{layer:1,type:side+"_LIMIT",entry,sl,tp:tp1},{layer:2,type:side+"_LIMIT",entry,sl,tp:tp2}]};
}
export function planDirectCopy(order, provider, receiver) {
 const type=String(order.type||"").toUpperCase(),types=["BUY","SELL","BUY_LIMIT","SELL_LIMIT","BUY_STOP","SELL_STOP","BUY_STOP_LIMIT","SELL_STOP_LIMIT"];
 if(!types.includes(type))throw Error("invalid order type");
 if(!order.orderId)throw Error("provider order id required");
 const source=scope(provider),dest=scope(receiver);
 return {mode:"DIRECT_MT5_COPY",provider:source,receiver:dest,providerOrderId:String(order.orderId),
  duplicateKey:JSON.stringify(["COPY",source,String(order.orderId),dest]),
  orders:[{type,symbol:String(order.symbol).toUpperCase(),entry:order.entry==null?null:norm(order.entry),sl:order.sl==null?null:norm(order.sl),tp:order.tp==null?null:norm(order.tp),volume:"RECEIVER_POLICY_REQUIRED"}]};
}
