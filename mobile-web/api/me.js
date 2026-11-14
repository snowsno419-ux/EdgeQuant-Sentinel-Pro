'use strict';
const {answer}=require('./_lib/core'),{db,signedIn}=require('./_lib/db');
module.exports=async(req,res)=>{if(req.method!=='GET')return answer(res,405,{error:'method_not_allowed'});if(!db())return answer(res,503,{error:'database_not_configured'});try{const u=await signedIn(req);return u?answer(res,200,{id:u.id,email:u.email,role:u.role,mode:'read_only'}):answer(res,401,{error:'sign_in_required'})}catch{return answer(res,503,{error:'database_unavailable'})}};
