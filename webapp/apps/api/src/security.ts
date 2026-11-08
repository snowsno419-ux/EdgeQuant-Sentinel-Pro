import {randomBytes, scrypt as scryptCallback, timingSafeEqual, createHash} from 'node:crypto';
import {promisify} from 'node:util';
const scrypt=promisify(scryptCallback);
const SCRYPT_N=16384, SCRYPT_R=8, SCRYPT_P=1;
export const SESSION_SECONDS=60*60*24*7;
export type Role='RECEIVER'|'PROVIDER'|'OWNER';
export function normalizeEmail(value:unknown):string {
 if(typeof value!=='string')throw Error('Invalid email');
 const email=value.trim().toLowerCase();
 if(email.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw Error('Invalid email');
 return email;
}
export function validatePassword(value:unknown):string {
 if(typeof value!=='string'||value.length<12||value.length>128)throw Error('Password must have 12–128 characters');
 return value;
}
export function validateSignupRole(value:unknown):'RECEIVER'|'PROVIDER' {
 if(value!=='RECEIVER'&&value!=='PROVIDER')throw Error('Public signup supports RECEIVER or PROVIDER only');
 return value;
}
export function validateTenantName(value:unknown):string {
 if(typeof value!=='string'||value.trim().length<2||value.trim().length>80)throw Error('Invalid display name');
 return value.trim();
}
export function validateBrokerIdentity(input:unknown):{server:string;login:string;label:string;isMain:boolean} {
 if(!input||typeof input!=='object'||Array.isArray(input))throw Error('Invalid broker account');
 const v=input as Record<string,unknown>;
 const server=typeof v.server==='string'?v.server.trim():'';
 const login=typeof v.login==='string'?v.login.trim():'';
 const label=typeof v.label==='string'?v.label.trim():'';
 if(!/^[\w .-]{3,100}$/.test(server)||!/^[0-9]{4,20}$/.test(login)||label.length>80||
   (v.isMain!==undefined&&typeof v.isMain!=='boolean'))throw Error('Invalid MT5 server/login/label');
 if(Object.keys(v).some(k=>/pass|secret|token|credential|api[_-]?key/i.test(k)))throw Error('Credentials not accepted here');
 return {server,login,label,isMain:v.isMain===true};
}
export async function hashPassword(password:string):Promise<string> {
 validatePassword(password);const salt=randomBytes(16);
 const hash=await scrypt(password,salt,64,{N:SCRYPT_N,r:SCRYPT_R,p:SCRYPT_P,maxmem:32*1024*1024}) as Buffer;
 return ['scrypt',String(SCRYPT_N),String(SCRYPT_R),String(SCRYPT_P),salt.toString('hex'),hash.toString('hex')].join(':');
}
export async function verifyPassword(password:unknown,encoded:string):Promise<boolean> {
 if(typeof password!=='string'||password.length>128||!encoded)return false;
 const parts=encoded.split(':');
 if(parts.length!==6||parts[0]!=='scrypt'||parts[1]!==String(SCRYPT_N)||parts[2]!==String(SCRYPT_R)||parts[3]!==String(SCRYPT_P))return false;
 try {
  const salt=Buffer.from(parts[4],'hex'),expected=Buffer.from(parts[5],'hex');
  if(salt.length!==16||expected.length!==64)return false;
  const actual=await scrypt(password,salt,64,{N:SCRYPT_N,r:SCRYPT_R,p:SCRYPT_P,maxmem:32*1024*1024}) as Buffer;
  return timingSafeEqual(expected,actual);
 }catch{return false;}
}
export function newOpaqueToken():{token:string;tokenHash:string} {
 const token=randomBytes(32).toString('base64url');return {token,tokenHash:hashToken(token)};
}
export function hashToken(token:string):string{return createHash('sha256').update(token,'utf8').digest('hex');}
export function assertRole(role:Role,allowed:readonly Role[]):void {
 if(!allowed.includes(role))throw Error('Forbidden');
}
