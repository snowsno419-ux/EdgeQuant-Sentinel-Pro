'use strict';
const {answer}=require('./_lib/core');
const {db}=require('./_lib/db');const {readyForRegistration,mailPolicy}=require('./_lib/onboarding');
const {readyForPasswordReset}=require('./_lib/password-reset');
const {botReady}=require('./_lib/telegram-bot');
module.exports=async function(req,res){
  if(req.method!=='GET')return answer(res,405,{error:'method_not_allowed'});
  const configured=!!process.env.DATABASE_URL;
  let ready=false, onboardingReady=false, telegramReady=false, telegramRequestReady=false, personalReady=false, requestReady=false, passwordResetSchema=false;
  if(configured){
    try{
      const pool=db();
      const r=await pool.query("SELECT (to_regclass('public.users') IS NOT NULL AND to_regclass('public.broker_accounts') IS NOT NULL AND to_regclass('public.sessions') IS NOT NULL AND to_regclass('public.worker_keys') IS NOT NULL AND to_regclass('public.broker_snapshots') IS NOT NULL) AS ready");
      ready=r.rows[0]?.ready===true;
      if(ready){const pw=await pool.query("SELECT to_regclass('public.password_reset_tokens') IS NOT NULL AS ready");passwordResetSchema=pw.rows[0]?.ready===true;const t=await pool.query("SELECT (to_regclass('public.verification_tokens') IS NOT NULL AND to_regclass('public.enrollment_sessions') IS NOT NULL AND to_regclass('public.auth_throttle') IS NOT NULL) AS onboarding, (to_regclass('public.telegram_sources') IS NOT NULL AND to_regclass('public.telegram_listener_keys') IS NOT NULL AND to_regclass('public.telegram_inbox') IS NOT NULL) AS telegram");onboardingReady=t.rows[0]?.onboarding===true;telegramReady=t.rows[0]?.telegram===true;const w=await pool.query("SELECT to_regclass('public.worker_provision_requests') IS NOT NULL AS ready");requestReady=w.rows[0]?.ready===true;const tgRequest=await pool.query("SELECT to_regclass('public.telegram_listener_requests') IS NOT NULL AS ready");telegramRequestReady=tgRequest.rows[0]?.ready===true;const personal=await pool.query("SELECT to_regclass('public.telegram_personal_dialogs') IS NOT NULL AS ready");personalReady=personal.rows[0]?.ready===true}
    }catch{ready=false}
  }
  return answer(res,200,{ok:true,service:'edgequant-cloud-api',version:'integration-0.3',database_configured:configured,database_ready:ready,auth_available:ready,registration_enabled:ready&&onboardingReady&&readyForRegistration(),registration_test_only:ready&&onboardingReady&&readyForRegistration()&&mailPolicy().testOnly,password_reset_ready:ready&&passwordResetSchema&&readyForPasswordReset(),telegram_inbox_ready:telegramReady,telegram_listener_request_ready:telegramRequestReady,telegram_personal_ready:ready&&telegramRequestReady&&personalReady,telegram_bot_configured:botReady(),mt5_pairing_available:ready,worker_request_ready:requestReady,mt5_worker_connected:false,telegram_connected:false,live_trade_execution:false,mode:'READ_ONLY_STAGE'});
};
