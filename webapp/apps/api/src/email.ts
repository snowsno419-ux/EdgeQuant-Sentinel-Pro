import nodemailer from 'nodemailer';
export function emailServiceConfigured():boolean {
 return Boolean(process.env.SMTP_URL)||(process.env.NODE_ENV!=='production'&&process.env.DEV_EMAIL_LOG==='1');
}
export async function sendVerificationEmail(to:string,token:string):Promise<void> {
 const baseUrl=process.env.WEB_ORIGIN||'http://localhost:3000';
 const link=baseUrl.replace(/\/$/,'')+'/verify?token='+encodeURIComponent(token);
 if(process.env.SMTP_URL) {
  const transport=nodemailer.createTransport(process.env.SMTP_URL);
  await transport.sendMail({from:process.env.MAIL_FROM||'EdgeQuant <no-reply@example.invalid>',to,
   subject:'Verify your EdgeQuant email',text:'Open this URL to verify your EdgeQuant account: '+link+'\nIf you did not create the account, ignore this email.'});
 } else if(process.env.NODE_ENV!=='production'&&process.env.DEV_EMAIL_LOG==='1') {
  console.log('[LOCAL DEVELOPMENT ONLY] Verification URL for '+to+': '+link);
 } else throw Error('SMTP not configured: email verification unavailable');
}
