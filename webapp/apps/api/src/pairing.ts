import {createHash,timingSafeEqual} from 'node:crypto';

export const PAIRING_TTL_MINUTES = 10;
export const AGENT_STALE_SECONDS = 120;
export type WorkerReport = {
  accountLogin:string;
  accountServer:string;
  terminalConnected:boolean;
  tradeAllowed:boolean;
};
export function authorizedBootstrap(bearer:unknown, configuredSecret:unknown):boolean {
  if(typeof configuredSecret!=='string'||configuredSecret.length<32||typeof bearer!=='string'||!bearer.startsWith('Bearer '))return false;
  const provided=bearer.slice(7);
  if(provided.length<32||provided.length>512)return false;
  const a=createHash('sha256').update(provided).digest();
  const b=createHash('sha256').update(configuredSecret).digest();
  return timingSafeEqual(a,b);
}
export function assertUuid(value:unknown):string {
  if(typeof value!=='string'||!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value))throw Error('Invalid broker account id');
  return value;
}
export function assertPairingToken(token:unknown):string {
  if(typeof token!=='string'||!/^[A-Za-z0-9_-]{43}$/.test(token))throw Error('Invalid pairing token');
  return createHash('sha256').update(token,'utf8').digest('hex');
}
export function parseWorkerReport(data:unknown):WorkerReport {
  if(!data||typeof data!=='object'||Array.isArray(data))throw Error('Invalid worker status');
  const v=data as Record<string,unknown>;
  if(typeof v.accountLogin!=='string'||!/^[0-9]{4,20}$/.test(v.accountLogin) ||
     typeof v.accountServer!=='string'||v.accountServer.length>100||v.accountServer.trim().length<3 ||
     typeof v.terminalConnected!=='boolean'||typeof v.tradeAllowed!=='boolean')throw Error('Invalid MT5 worker report');
  return {accountLogin:v.accountLogin,accountServer:v.accountServer.trim(),terminalConnected:v.terminalConnected,tradeAllowed:v.tradeAllowed};
}
export function accountIdentityMatches(expected:{server:string;login:string}, observed:{accountServer:string;accountLogin:string}):boolean {
  return expected.login===observed.accountLogin && expected.server.trim().toLowerCase()===observed.accountServer.trim().toLowerCase();
}
export function visiblePairingStatus(persisted:string,lastSeen:Date|string|null,nowMs=Date.now()):string {
  if(persisted!=='CONNECTED')return persisted;
  if(!lastSeen)return 'DISCONNECTED';
  const seenMs=new Date(lastSeen).getTime();
  if(!Number.isFinite(seenMs)||seenMs>nowMs+30_000||nowMs-seenMs>AGENT_STALE_SECONDS*1000)return 'DISCONNECTED';
  return 'CONNECTED';
}
