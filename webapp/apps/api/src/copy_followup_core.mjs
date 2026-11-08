/** Phase 7: fail-closed, DEMO-only, original-receiver-ticket MODIFY/CANCEL contract. */
export const FOLLOWUP_ACTIONS=Object.freeze(['MODIFY','CANCEL']);
export const FOLLOWUP_LEASE_SECONDS=90;
const decimal=s=>typeof s==='string' && /^\d{1,12}(?:\.\d{1,8})?$/.test(s) && Number(s)>0;
const ticket=s=>typeof s==='string' && /^[1-9][0-9]{0,18}$/.test(s);
const token=s=>typeof s==='string' && /^[A-Za-z0-9_-]{43}$/.test(s);
const uuid=s=>typeof s==='string' && /^[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$/.test(s);
export function sanitizePendingFollowup(delivery) {
 if(!delivery||typeof delivery!=='object'||Array.isArray(delivery)||!FOLLOWUP_ACTIONS.includes(delivery.action) || !['STAGED','WAITING_TICKET_MAPPING'].includes(delivery.status))throw Error('Only pending MODIFY/CANCEL intents supported');
 const request=delivery.request;
 if(!request||typeof request!=='object'||Array.isArray(request))throw Error('Request required');
 if(!ticket(request.ticket))throw Error('Mapped receiver pending ticket required');
 if(delivery.action==='CANCEL'){
  if(Object.keys(request).some(k=>k!=='ticket'))throw Error('Unexpected CANCEL field');
  return Object.freeze({action:'CANCEL',ticket:request.ticket});
 }
 if(!request.changes||typeof request.changes!=='object'||Array.isArray(request.changes))throw Error('MODIFY requires changes');
 const changes=request.changes;
 if(Object.keys(changes).length===0||Object.keys(changes).some(k=>!['entry','sl','tp'].includes(k)))throw Error('Unexpected MODIFY fields');
 for(const [k,v] of Object.entries(changes)){
  if(k==='entry' ? !decimal(v) : v!==null&&!decimal(v))throw Error('Invalid '+k+' update');
 }
 if(Object.keys(request).some(k=>!['ticket','changes'].includes(k)))throw Error('Unexpected MODIFY request field');
 return Object.freeze({action:'MODIFY',ticket:request.ticket,changes:Object.freeze({...changes})});
}
export function validatedFollowupLease(delivery,account,origin) {
 if(!delivery||delivery.source!=='DIRECT_MT5_COPY'||delivery.demoOnly!==true||!uuid(delivery.id)||!token(delivery.leaseToken))throw Error('Invalid broker lease');
 if(!account||!origin||String(delivery.accountLogin)!==String(account.login)||String(delivery.accountServer).toLowerCase()!==String(account.server).toLowerCase())throw Error('Wrong broker account');
 if(!uuid(delivery.originalOpenDeliveryId)||!ticket(delivery.receiverTicket)||!ticket(delivery.providerTicket))throw Error('Original mapping invalid');
 const expected=sanitizePendingFollowup({action:delivery.action,status:'STAGED',request:delivery.request});
 if(expected.ticket!==delivery.receiverTicket)throw Error('Mapped ticket mismatch');
 if(delivery.originalOpenDeliveryId===delivery.id)throw Error('Followup cannot be its OPEN');
 return Object.freeze({...expected,originalOpenDeliveryId:delivery.originalOpenDeliveryId});
}
export function sanitizeFollowupAck(value) {
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Invalid ACK');
 if(Object.keys(value).some(k=>!['status','leaseToken','brokerRetcode','brokerMessage'].includes(k)))throw Error('Unknown ACK field');
 if(!['BROKER_ACCEPTED','BROKER_REJECTED','LOCAL_REJECTED','UNKNOWN_RECONCILE'].includes(value.status)||!token(value.leaseToken))throw Error('Invalid ACK state or token');
 if(value.brokerRetcode!==undefined&&value.brokerRetcode!==null&&(!Number.isSafeInteger(value.brokerRetcode)||value.brokerRetcode<0||value.brokerRetcode>999999))throw Error('Invalid broker retcode');
 if(value.brokerMessage!==undefined&&(typeof value.brokerMessage!=='string'||value.brokerMessage.length>320))throw Error('Invalid broker message');
 return Object.freeze({status:value.status,leaseToken:value.leaseToken,brokerRetcode:value.brokerRetcode??null,brokerMessage:value.brokerMessage??''});
}
