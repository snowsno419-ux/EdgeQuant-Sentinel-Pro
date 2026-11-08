# EdgeQuant Installer - Error Code 15 diagnosis (2026-11-06)

User screenshot path referenced the OLD folder `EdgeQuant_Telegram_Login_SendCode_Fix_20261106`. That folder does not contain recent installer fixes. Always unpack THIS complete ZIP into a brand new directory, e.g. `C:\EQBuild15\EdgeQuant`, without merging it with prior versions.

**What code 15 means:** `BUILD-CLIENT-INSTALLER-CORE.bat` detected an Inno Setup compiler failure or did not find `dist\EdgeQuant-Sentinel-Client-Setup.exe`. Without the actual `ISCC.exe` compiler output, it is impossible to claim which specific syntax/file/permission problem occurred on that Windows PC.

**Changes here**:
- `COMPILE-INNO-DIAGNOSTICS.ps1` runs the real Inno Setup compiler without `/Qp`, captures its full output to `INNO-COMPILER-ERROR.log`, and shows the actual errors on screen.
- Checks that frozen app, icon and .iss exist, that dist has no un-scrubbed Python source/session files, and that a previous installer exe is not locked.
- `SHOW-INNO-ERROR.bat` displays the last 100 lines.
- Inno compressor is `lzma2/max` rather than `lzma2/ultra64`, reducing memory pressure during installer generation.
- No trading, Telegram or broker execution logic changed.
- All batch files in the project retain CRLF endings.

**Build**: Run `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` from inside the new extracted EdgeQuant folder. If code 15 remains, run `SHOW-INNO-ERROR.bat`, then share the **specific** `INNO-COMPILER-ERROR.log` (without any tokens/accounts) so the compiler's precise failure can be fixed. Do not distribute an unverified Setup.exe or any raw `dist` directory.

**Limitations:** Static source inspection and offline Python tests on Linux are not a Windows Inno Setup compilation. The installer has not been built or tested under Windows here.
