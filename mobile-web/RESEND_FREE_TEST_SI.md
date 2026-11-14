# EdgeQuant — Resend FREE test-email mode (Sinhala)
Public customer registration and MT5 live trading stay OFF until verified.
1. Sign in to https://resend.com. The `onboarding@resend.dev` shared sender may email **only the same email address belonging to the Resend account**. It is NOT a real sending domain for clients.
2. Create a *sending-only* Resend API key at https://resend.com/api-keys. Put it in **Vercel → edgequant-mobile-web → Settings → Environment Variables** as **Production / Encrypted** `RESEND_API_KEY`. Never paste it into a public repo, browser or ChatGPT chat. Vercel Marketplace Resend installation being present on the account does not mean a key was connected to this project.
3. This project has `EQ_MAIL_FROM=EdgeQuant Test <onboarding@resend.dev>` and `EQ_SIGNUP_TEST_ONLY=1` for Production. Set `EQ_TEST_EMAIL` to the email of the account signed into Resend, as a Production env var. Do not use any client's address.
4. Redeploy after adding env vars. Confirm `/api/health`: `database_ready:true`, `registration_enabled:false` while `EQ_SIGNUP_ENABLED=0`.
5. Only when you are ready to test **your one test inbox**, temporarily set `EQ_SIGNUP_ENABLED=1`; redeploy, verify `registration_enabled:true` and `registration_test_only:true`. Submit signup with the same `EQ_TEST_EMAIL`. Other email addresses must be rejected.
6. Check that mail arrives, verify one-use 20-minute token, set up TOTP, log in, log out, then set `EQ_SIGNUP_ENABLED=0` again for production while onboarding is still in development.
7. To go public later, buy and verify a domain, switch sender to that verified domain, remove test-only mode, test again and review security/abuse protection. Do not do this automatically.
More: https://resend.com/changelog/sending-test-emails
