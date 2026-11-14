'use strict';
const {answer}=require('./_lib/core');
module.exports=async(req,res)=>{if(req.method!=='GET')return answer(res,405,{error:'method_not_allowed'});return answer(res,200,{ok:true,service:'edgequant-cloud-api',version:'integration-0.1',database_configured:!!process.env.DATABASE_URL,auth_available:!!process.env.DATABASE_URL,mt5_worker_connected:false,telegram_connected:false,live_trade_execution:false,mode:'READ_ONLY_STAGE'})};
