'use strict';const {sha,parseCookies}=require('./core');
async function enrollment(pool,req){const t=parseCookies(req.headers.cookie)['__Host-eq_enroll'];if(!t||!/^[A-Za-z0-9_-]{40,150}$/.test(t))return null;const q=await pool.query('SELECT user_id FROM enrollment_sessions WHERE token_digest=$1 AND expires_at>NOW()',[sha(t)]);return q.rows[0]||null}
module.exports={enrollment};
