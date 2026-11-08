/** Phase 6: DEMO-only Direct MT5 Copy pending-order OPEN contract. */
export const SUPPORTED_DEMO_COPY_TYPES=Object.freeze(['BUY_LIMIT','SELL_LIMIT','BUY_STOP','SELL_STOP']);
export const COPY_LEASE_SECONDS=90;
const validToken=v=>typeof v==='string'&&/^[A-Za-z0-9_-]{43}$/.test(v);
const positivePrice=v=>typeof v==='string'&&/^\d{1,12}(?:\.\d{1,8})?$/.test(v)&&Number(v)>0;
export function sanitizeCopyDemoRequest(plan) {
 if(!plan||typeof plan!=='object'||Array.isArray(plan)||plan.action!=='OPEN'||plan.status!=='STAGED')throw Error('Only staged OPEN events eligible');
 const order=plan.request;
 if(!order||typeof order!=='object'||Array.isArray(order)||!SUPPORTED_DEMO_COPY_TYPES.includes(order.type))throw Error('Only pending LIMIT/STOP copy allowed in Phase 6');
 if(!/^[A-Z0-9._-]{3,32}$/.test(order.symbol||'')||!positivePrice(order.entry)||!positivePrice(order.volume))throw Error('Invalid pending copy symbol/entry/volume');
 if(order.sl!==null&&order.sl!==undefined&&!positivePrice(order.sl))throw Error('Invalid SL');
 if(order.tp!==null&&order.tp!==undefined&&!positivePrice(order.tp))throw Error('Invalid TP');
 if(order.brokerPriceMayDiffer)throw Error('Market executions disabled');
 return Object.freeze({type:order.type,symbol:order.symbol,entry:order.entry,
  sl:order.sl??null,tp:order.tp??null,volume:order.volume});
}
export function sanitizeCopyDemoAck(data) {
 if(!data||typeof data!=='object'||Array.isArray(data))throw Error('Invalid copy acknowledgement');
 const allowed=new Set(['BROKER_ACCEPTED','BROKER_REJECTED','LOCAL_REJECTED','UNKNOWN_RECONCILE']);
 if(!allowed.has(data.status)||!validToken(data.leaseToken))throw Error('Invalid lease/status');
 if(Object.keys(data).some(k=>!['status','leaseToken','brokerTicket','brokerRetcode','brokerMessage'].includes(k)))throw Error('Unexpected copy acknowledgement fields');
 const ticket=data.brokerTicket??null;
 if(ticket!==null&&!(typeof ticket==='string'&&/^[1-9][0-9]{0,18}$/.test(ticket)))throw Error('Invalid receiver ticket');
 if(data.status==='BROKER_ACCEPTED'&&!ticket)throw Error('Accepted broker order must have receiver ticket');
 if(data.status!=='BROKER_ACCEPTED'&&ticket!==null)throw Error('Only accepted order may carry broker ticket');
 const retcode=data.brokerRetcode??null;
 if(retcode!==null&&(!Number.isInteger(retcode)||retcode<0||retcode>999999))throw Error('Invalid retcode');
 const message=String(data.brokerMessage??'');
 if(message.length>320)throw Error('Broker message too long');
 return Object.freeze({status:data.status,leaseToken:data.leaseToken,brokerTicket:ticket,brokerRetcode:retcode,brokerMessage:message});
}
