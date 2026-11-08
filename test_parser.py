"""Run with:  python3 test_parser.py   (no third-party packages needed)"""
from signal_parser import parse_signal

HINTS = {
    "XAUUSD": 2652.0, "EURUSD": 1.0855, "GBPUSD": 1.2860, "USDCAD": 1.3605,
    "US30": 42480.0, "GBPJPY": 188.40, "AUDUSD": 0.6560, "XAGUSD": 31.60,
    "USOIL": 71.20, "BTCUSD": 63000.0,
}

SYMBOLS = list(HINTS.keys())

CASES = [
    # (message, expectations dict)
    ("XAUUSD BUY LIMIT 2650\nSL 2640\nTP 2660\nTP2 2670",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[2650.0], sl=2640.0, tps=[2660.0, 2670.0], confidence="high")),

    ("🟢 EURUSD BUY LIMIT @ 1.0850\nSL: 1.0800   TP: 1.0900",
     dict(symbol="EURUSD", direction="BUY", order_type="LIMIT", entries=[1.0850],
          sl=1.0800, tps=[1.0900])),

    ("Sell Limit GOLD 2675-2678   SL 2685   TP 2665",
     dict(symbol="XAUUSD", direction="SELL", order_type="LIMIT",
          entries=[2675.0, 2678.0], sl=2685.0, tps=[2665.0])),

    ("USDCAD SELL LIMIT\nEntry: 1.3620\nSL: 50 pips\nTP: 100 pips",
     dict(symbol="USDCAD", direction="SELL", order_type="LIMIT", entries=[1.3620],
          sl=1.3670, tps=[1.3520])),

    ("🔴 US30 SELL LIMIT 42500 SL 42650 TP 42200",
     dict(symbol="US30", direction="SELL", order_type="LIMIT", entries=[42500.0],
          sl=42650.0, tps=[42200.0])),

    ("BUY LIMIT GBPJPY 188.50, SL 187.80, TP 189.50, lot 0.10",
     dict(symbol="GBPJPY", direction="BUY", order_type="LIMIT", entries=[188.5],
          sl=187.8, tps=[189.5], volume=0.10)),

    ("XAUUSD SELL LIMIT 2.678,50 SL 2.690,00 TP 2.650,00",
     dict(symbol="XAUUSD", direction="SELL", order_type="LIMIT", entries=[2678.5],
          sl=2690.0, tps=[2650.0])),

    ("AUDUSD buy limit 0,6550 sl 0,6500 tp 0,6620",
     dict(symbol="AUDUSD", direction="BUY", order_type="LIMIT", entries=[0.655],
          sl=0.65, tps=[0.662])),

    # tricky: UK decimal comma, needs the live-price hint to resolve
    ("GBPUSD BUY LIMIT 1,285 SL 1,280 TP 1,295",
     dict(symbol="GBPUSD", direction="BUY", order_type="LIMIT", entries=[1.285],
          sl=1.28, tps=[1.295])),

    ("XAUUSD BUY 2652 SL 2645 TP 2660",
     dict(symbol="XAUUSD", direction="BUY", order_type="LIMIT", entries=[2652.0])),

    ("CANCEL ALL PENDING EURUSD",
     dict(action="cancel_pending", symbol="EURUSD")),

    ("CLOSE ALL POSITIONS NOW",
     dict(action="close_all")),

    # ---- follow-up / management messages ----------------------------------
    ("Move SL to breakeven on XAUUSD",
     dict(action="move_be", symbol="XAUUSD")),

    ("Cancel the pending order on GOLD, entry missed",
     dict(action="cancel_pending", symbol="XAUUSD")),

    ("Entry missed, cancel it",
     dict(action="cancel_pending")),

    ("Close half of the position on GOLD",
     dict(action="close_partial", symbol="XAUUSD", fraction=0.5)),

    ("Book 50% here and move SL to BE",
     dict(action="close_partial", fraction=0.5, be_pips=0.0)),

    ("Secure 25% on XAUUSD",
     dict(action="close_partial", symbol="XAUUSD", fraction=0.25)),

    ("Trail the trade now",
     dict(action="unsupported")),

    # ---- current-market (CJ FX style) channels -----------------------------
    ("GOLD\nBUY\nENTER NOW\n\u2764\ufe0f4 \U0001F5252",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="MARKET",
          entries=[])),

    ("\U0001F7E2 BUY\n$ GOLD\n\U0001F4CA ENTER IN = 4185- 4178\n"
     "\U0001F534 SL = 4177 (80 pips )\n"
     "\U0001F3AF TP1 = 4190\n\U0001F3AF TP2 = 4230\n\U0001F3AF TP3 = 4250\n"
     "\U0001F7E2 After Hit TP1 , Move SL to Entry \U0001F525",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[4185.0, 4178.0], sl=4177.0, tps=[4190.0, 4230.0, 4250.0],
          be_after_tp1=True, entry_marked=True)),

    ("\U0001F4ABGOLD SEll SIGNAL \U0001F4AB\n\n\U0001F534ENTRY:4186\n\n"
     "\U0001F3AF TARGET 1: 4183\u2705\n\U0001F3AF TARGET 2: 4180\u2705\n"
     "\U0001F3AF TARGET 3: 4177\u2705\n\n\U0001F480STOP LOSS: 4200\n\n"
     "After TP1 is reached, secure your position and move SL \u2192 BREAKEVEN (BE).",
     # channel default is MARKET -> the listener then turns it into a LIMIT entry
     dict(action="place", symbol="XAUUSD", direction="SELL", order_type="LIMIT",
          entries=[4186.0], sl=4200.0, tps=[4183.0, 4180.0, 4177.0],
          be_after_tp1=True, entry_marked=True)),

    # ---- TEST LIMIT CHANNEL channel: TP change + single entries ---------------
    ("Change All Sell Trades To TP 4135",
     dict(action="modify_tp", direction="SELL", scope="positions", tp=4135.0)),

    ("Move all buy trades TP to 4200",
     dict(action="modify_tp", direction="BUY", scope="positions", tp=4200.0)),

    ("Change All Sell Trades To BE",
     dict(action="move_be", direction="SELL", scope="positions")),

    ("Change all pending orders to TP 4180",
     dict(action="modify_tp", scope="pending", tp=4180.0)),

    # single-entry signals (no range) + pasted telegram timestamp prefix
    ("[10/5/2026 6:23 AM] TEST LIMIT CHANNEL: GOLD BUY 4139-4136\n\nSL 4133\n\nTP 4159",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[4139.0, 4136.0], sl=4133.0, tps=[4159.0])),

    ("GOLD BUY 4124\n\nSL 4117\n\nTP 4159",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[4124.0], sl=4117.0, tps=[4159.0])),

    ("GOLD SELL 4154\n\nSL 4160\n\nTP 4129\n\n"
     "( or You can BE on 70 Pips And The n Break out happened hold Below 4236 )",
     dict(action="place", symbol="XAUUSD", direction="SELL", order_type="LIMIT",
          entries=[4154.0], sl=4160.0, tps=[4129.0], be_pips=70.0)),

    # This live channel writes its entry zone as two space-separated prices.
    ("GOLD SELL 4173 4177\nTP 4170\nTP 4166\nTP 4162\nTP 4158\nTP 4155\nSL 4185",
     dict(action="place", symbol="XAUUSD", direction="SELL", entries=[4173.0, 4177.0],
          sl=4185.0, tps=[4170.0, 4166.0, 4162.0, 4158.0, 4155.0])),

    # TP/profit recaps must not become fresh entries from an emoji or bare price.
    ("4179 Hit 📈 80 Pips Done",
     dict(action="ignore", direction="BUY", entries=[4179.0], confidence="high")),

    ("40 Pips Done💸", dict(action="ignore")),

    ("BUY 4179 — TP hit, 80 pips done",
     dict(action="ignore", direction="BUY", entries=[4179.0], confidence="high")),

    # Clear fresh-entry structure still permits a legitimate signal with recap text.
    ("XAUUSD BUY LIMIT @ 4179\nSL 4169\nTP 4200\nPrevious TP hit; 80 pips done",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[4179.0], sl=4169.0, tps=[4200.0])),

    ("Good morning traders, weekly outlook attached below 👇",
     dict(action="ignore")),

    ("XAGUSD SELL LIMIT 31.80\nSL 32.20\nTP 31.20\nSL pips: no wait ignore this line",
     dict(symbol="XAGUSD", direction="SELL", entries=[31.8], sl=32.2, tps=[31.2])),

    # ---- real TWGM VIP Signal (limit channel) messages --------------------
    # entry comes as a RANGE in written order: near edge first, deep edge second
    ("TWGM VIP Signal\nGOLD BUY 4155-4143\n\nSL 4135\n\nTP 4199\n\n"
     "( or You can BE on 70 Pips And The n Break out happened hold Above 4389 )",
     dict(action="place", symbol="XAUUSD", direction="BUY", order_type="LIMIT",
          entries=[4155.0, 4143.0], sl=4135.0, tps=[4199.0], be_pips=70.0)),

    ("TWGM VIP Signal\nGOLD SELL 4176-4182\n\nSL 4192\n\nTP 4145\n\n"
     "( or You can BE on 70 Pips And The n Break out happened hold Below 4236 )",
     dict(action="place", symbol="XAUUSD", direction="SELL", order_type="LIMIT",
          entries=[4176.0, 4182.0], sl=4192.0, tps=[4145.0])),

    ("TWGM VIP Signal\nGOLD SELL 4147-4153\n\nSL 4160\n\nTP 4101\n\n"
     "( or you can BE on 70 Pips And The n Break out happened hold Below 4236 )",
     dict(action="place", symbol="XAUUSD", direction="SELL", order_type="LIMIT",
          entries=[4147.0, 4153.0], sl=4160.0, tps=[4101.0], be_pips=70.0)),

    ("GOOD MORNING FRIENDS", dict(action="ignore")),
]

UNIVERSE = ["XAUUSD.m", "EURUSD.m", "GBPUSD.m", "USDJPY.m", "USDCAD.m", "US30.m",
            "GBPJPY.m", "AUDUSD.m", "XAGUSD.m", "USOIL.m", "BTCUSD.m"]


def main() -> int:
    failed = 0
    for i, (msg, exp) in enumerate(CASES, 1):
        sig = parse_signal(msg, symbols=UNIVERSE, hint_prices=HINTS)
        bad = []
        for k, want in exp.items():
            got = getattr(sig, k)
            if isinstance(want, list):
                ok = got[:len(want)] == want and len(got) == len(want)
            elif isinstance(want, float):
                ok = got is not None and abs(got - want) < 1e-6
            else:
                ok = got == want
            if not ok:
                bad.append(f"{k}: want {want!r} got {got!r}")
        status = "PASS" if not bad else "FAIL"
        if bad:
            failed += 1
        print(f"[{status}] case {i}: {msg.splitlines()[0][:60]!r}")
        print(f"        -> action={sig.action} {sig.symbol} {sig.direction} {sig.order_type} "
              f"entries={sig.entries} sl={sig.sl} tps={sig.tps} vol={sig.volume} conf={sig.confidence}")
        if sig.issues:
            print(f"        issues: {sig.issues}")
        for b in bad:
            print(f"        !! {b}")

    # Reproduce the exact channel defaults from the incident screenshot.
    incident = parse_signal(
        "4179 Hit 📈 80 Pips Done", default_order_type="MARKET", default_symbol="XAUUSD")
    incident_ok = (
        incident.action == "ignore" and incident.symbol == "XAUUSD"
        and incident.direction == "BUY" and incident.entries == [4179.0]
        and incident.confidence == "high"
        and any("TP/result" in note for note in incident.notes)
    )
    incident_status = "PASS" if incident_ok else "FAIL"
    print(f"[{incident_status}] exact incident with MARKET/XAUUSD defaults")
    if not incident_ok:
        failed += 1
        print(f"        !! got action={incident.action} symbol={incident.symbol} "
              f"direction={incident.direction} entries={incident.entries} "
              f"confidence={incident.confidence} notes={incident.notes}")

    total = len(CASES) + 1
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
