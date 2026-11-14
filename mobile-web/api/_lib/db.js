'use strict';
const {sha,parseCookies}=require('./core');let pool;
function db(){if(!process.env.DATABASE_URL)return null;if(!pool){const {Pool}=require('pg');pool=new Pool({connectionString:process.env.DATABASE_URL,max:3,connectionTimeoutMillis:4000,idleTimeoutMillis:10000,ssl:process.env.EQ_DB_SSL==='disable'?false:{rejectUnauthorized:true}})}return pool}
async function signedIn(req){const v=parseCookies(req.headers.cookie)['__Host-eq_session'];if(!v||!/^[A-Za-z0-9_-]{30,200}$/.test(v))return null;const r=await db().query('SELECT u.id,u.email,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_digest=$1 AND s.expires_at>NOW() AND u.email_verified=TRUE',[sha(v)]);return r.rows[0]||null}
module.exports={db,signedIn};
