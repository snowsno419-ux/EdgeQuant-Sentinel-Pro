@echo off
cd /d "%~dp0"
python -m unittest -v test_scoped_multilingual_signal_updates_20261106 test_multilang_engine_dispatch_20261106 test_owner_direct_limit_20261106
pause
