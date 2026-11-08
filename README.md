# EdgeQuant Sentinel Pro

Private development repository for the EdgeQuant Sentinel desktop-to-cloud migration.

## Current status
This repository is an **implementation handoff**, not a completed cloud trading SaaS or production-ready web application.

## Upload the existing project from your PC
1. Open the downloaded/extracted `EdgeQuant_Cloud_Mobile_NoPC_Handoff_Kit_20261107` folder.
2. Extract `02_CURRENT_EDGEQUANT_SOURCE.zip` into a separate folder.
3. Upload its source files and folders into this repository, alongside the following handoff documents:
   - `01_MASTER_PROMPT_SI.md`
   - `03_V2_ARCHITECTURE_PLAN.md`
   - `05_PC_FREE_MANAGED_CLOUD_SI.md`
4. Do **not** upload `.env`, Telegram `.session` files, passwords, account credentials, API keys or customer trade records.

## Target
A mobile-first multi-tenant cloud application using managed isolated Windows/MT5 execution workers for clients without PCs, while preserving the existing signal execution and risk rules.

## Safety
Use a demo MT5 account for all execution testing before any live deployment. Never upload client credentials or sensitive data to this repository.
