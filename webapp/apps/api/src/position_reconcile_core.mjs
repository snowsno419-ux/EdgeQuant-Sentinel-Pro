/** Phase 7B position evidence, not permission for close/partial-close trading. */
const TICKET=/^[1-9][0-9]{0,18}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const POSITION_OBSERVATIONS=Object.freeze(['STILL_PENDING','FILLED_POSITION_OBSERVED','UNKNOWN_RECONCILE']);
export function validatePositionObservation(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('Object expected');
 const allowed=new Set(['mappingId','receiverOrderTicket','status','positionIdentifier','positionTicket','volume','reason']);
 if(Object.keys(raw).some(k=>!allowed.has(k)))throw Error('Unexpected observation field');
 if(!UUID.test(raw.mappingId)||!TICKET.test(raw.receiverOrderTicket)||!POSITION_OBSERVATIONS.includes(raw.status))throw Error('Invalid position observation identity/status');
 if(typeof raw.reason!=='string'||!raw.reason.length||raw.reason.length>180)throw Error('Invalid observation reason');
 if(raw.status==='FILLED_POSITION_OBSERVED'){
  if(!TICKET.test(raw.positionIdentifier)||!TICKET.test(raw.positionTicket)||typeof raw.volume!=='string'||
     !/^\d{1,12}(?:\.\d{1,8})?$/.test(raw.volume)||Number(raw.volume)<=0)throw Error('Missing verified position id/ticket/volume');
 }else if(raw.positionIdentifier!=null||raw.positionTicket!=null||raw.volume!=null)throw Error('Never attach position ticket to unverified observation');
 return Object.freeze({mappingId:raw.mappingId,receiverOrderTicket:raw.receiverOrderTicket,status:raw.status,
  positionIdentifier:raw.positionIdentifier??null,positionTicket:raw.positionTicket??null,
  volume:raw.volume??null,reason:raw.reason});
}
export function choosePositionEvidence(previous, incoming){
 const r=validatePositionObservation(incoming);
 if(!previous)return 'RECORD_NEW';
 if(previous.receiverOrderTicket!==r.receiverOrderTicket)throw Error('Order ownership conflict');
 if(previous.status==='FILLED_POSITION_OBSERVED'&&r.status==='FILLED_POSITION_OBSERVED'&&
    (previous.positionIdentifier!==r.positionIdentifier||previous.positionTicket!==r.positionTicket)){
     return 'HOLD_MAPPING_CONFLICT';
 }
 if(previous.status==='FILLED_POSITION_OBSERVED'&&r.status==='STILL_PENDING')return 'HOLD_REGRESSION';
 return 'RECORD_UPDATE';
}
export function classifyCloseReadiness(mapping){
 if(!mapping||mapping.state!=='FILLED_HOLD'||!TICKET.test(String(mapping.filled_position_identifier||'')))
   return {ready:false,reason:'Pending-to-position reconciliation incomplete'};
 return {ready:false,reason:'Position close executor is deliberately disabled in Phase 7B1; broker-level netting, close volume and order lifecycle tests outstanding'};
}
