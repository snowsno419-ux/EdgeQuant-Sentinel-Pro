@echo off
cd /d "%~dp0"
python -m unittest -q test_trade_limits_ai_agent_removed_20261106 test_owner_direct_limit_20261106 test_multilang_engine_dispatch_20261106 test_scoped_multilingual_signal_updates_20261106 test_telegram_code_guard test_telegram_reconnect
pause
