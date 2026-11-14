'use strict';
const {answer}=require('./_lib/core');
const {db}=require('./_lib/db');
module.exports=async function(req,res){
  if(req.method!=='GET')return answer(res,405,{error:'method_not_allowed'});
  const configured=!!process.env.DATABASE_URL;
  let ready=false;
  if(configured){
    try{
      const pool=db();
      const r=await pool.query("SELECT (to_regclass('public.users') IS NOT NULL AND to_regclass('public.broker_accounts') IS NOT NULL AND to_regclass('public.sessions') IS NOT NULL AND to_regclass('public.worker_keys') IS NOT NULL AND to_regclass('public.broker_snapshots') IS NOT NULL) AS ready");
      ready=r.rows[0]?.ready===true;
    }catch{ready=false}
  }
  return answer(res,200,{ok:true,service:'edgequant-cloud-api',version:'integration-0.2',database_configured:configured,database_ready:ready,auth_available:ready,mt5_worker_connected:false,telegram_connected:false,live_trade_execution:false,mode:'READ_ONLY_STAGE'});
};
