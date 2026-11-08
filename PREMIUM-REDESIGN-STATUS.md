# EdgeQuant Sentinel Pro - premium workspace iteration

This package updates the existing Tkinter desktop UI, not the MT5 trading engine.

Changed:
- Six top-of-dashboard KPI cards (balance, equity, floating P&L, pending, open positions if verifiable, MT5 status).
- A new compact dashboard control deck with Channels, Trade Journal and Today's Report navigation.
- Wider sidebar, refreshed dashboard identity and a less oversized MT5 account header.
- Launcher prefers Python 3.12 with MetaTrader5 available and shows startup errors in a console.

Unchanged:
- edgequant_auto.py trading engine (verified SHA-256 match with input archive).
- Telegram signal routing, risk controls, limit order and break-even execution logic.
- Existing specialist pages remain available from the sidebar.

Verification: Python syntax compilation and two focused unit tests pass. Windows GUI and live MT5/Telegram integration are not tested here.

This is a real layout change but NOT a pixel-perfect implementation of the approved mockup. The specialist pages still use their existing widgets and need a separate full redesign.
