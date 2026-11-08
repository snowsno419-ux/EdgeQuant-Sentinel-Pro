# EdgeQuant client installer: missing `cryptography` fixed (6 Nov 2026)

## Cause
The original `BUILD-CLIENT-INSTALLER-CORE.bat` called `python -m unittest` before installing the dependencies of `test_edgequant_remote_agent.py`. `requirements.txt` omitted `cryptography` and `requests` although `edgequant_remote_agent.py` requires both; the project could fail with `ModuleNotFoundError: No module named cryptography` and build error 9.

## Fix
- `requirements.txt` now lists `cryptography>=44,<47` and `requests>=2.31,<3`.
- `requirements-build.txt` includes both app requirements and PyInstaller/test build dependencies.
- `PREPARE-CLIENT-BUILD-ENV.bat` uses a private `.edgequant-build-venv` and installs/verifies dependencies **before running any tests**. It prefers Python 3.11, then 3.12, 3.13, 3.14 x64, and does not use incompatible Python 3.15. Build errors are clearly reported; failed tests are never bypassed.
- `BUILD-CLIENT-INSTALLER-CORE.bat` calls the prepare script, adds the venv to `PATH`, then runs the entire unittest suite, syntax checks and subsequent original installer/scrub steps.
- Standalone `BUILD-EXE.bat` uses the same `requirements-build.txt` dependency manifest.
- `RUN-CURRENT-RELEASE-TESTS.bat` also prepares dependencies first.

## Windows build
1. Extract the ZIP to `C:\EdgeQuantBuild` (do not run inside ZIP), make sure **Inno Setup 6** is installed.
2. Install 64-bit Python **3.11** with Tkinter/Tcl/Tk, venv, pip and Python Launcher (`py`). 3.12-3.14 are also supported by the preparation script. Python 3.15 is *not supported for this MT5 build* because MetaTrader5 5.0.6231 has Windows wheels only through CPython 3.14.
3. Double-click `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` with internet access. Pip installation output appears in the persistent CMD and `CLIENT-INSTALLER-BUILD.log`.
4. Python packages install into `.edgequant-build-venv`, not globally. The same environment is used for tests and PyInstaller. Keep the terminal open until completion.
5. Only distribute `dist\EdgeQuant-Sentinel-Client-Setup.exe` after a successful build and **clean Windows PC + MT5 Demo** check. Never distribute ZIP or private config/session files.

## Failure troubleshooting
- Missing Inno Setup: install Inno Setup 6.
- `Python 3.11 ... not found`: install 64-bit Python 3.11 and re-run. If a previous `.edgequant-build-venv` used the wrong Python, rename/remove **only that generated build-venv folder** and re-run.
- Pip network/version error: review full pip message in build log; check access to PyPI and re-run. Do not ignore dependency failures.
- `MetaTrader5` installation error: the Windows build interpreter must match a supported wheel (3.11 recommended); fix Python before continuing.

## Validation
Offline current-release regression suite and Python syntax checks were executed in a non-Windows environment. Windows venv provisioning, MT5 native module, PyInstaller, Inno Setup compilation, and live account use need checking on Windows. These files never claim to disable broker-side trading requirements or to guarantee order acceptance.
