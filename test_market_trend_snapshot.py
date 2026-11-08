import edgequant_auto as engine


class FakeMT5:
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        # Deterministic rising close series: expected bullish EMA structure.
        return [{"close": 1900.0 + i * 0.25} for i in range(100)]


def test_trend_snapshot_reports_each_requested_timeframe(monkeypatch):
    monkeypatch.setattr(engine, "mt5_connection_probe", lambda api: {"ready": True})
    result = engine.mt5_provider_trend_snapshot("XAUUSD", mt5_api=FakeMT5())
    assert result["status"] == "connected"
    assert set(result["timeframes"]) == {"M5", "M15", "H1", "H4"}
    assert all(row["trend"] == "BULLISH" for row in result["timeframes"].values())


def test_trend_snapshot_handles_missing_candles(monkeypatch):
    class EmptyMT5(FakeMT5):
        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            return []

    monkeypatch.setattr(engine, "mt5_connection_probe", lambda api: {"ready": True})
    result = engine.mt5_provider_trend_snapshot("XAUUSD", mt5_api=EmptyMT5())
    assert result["status"] == "connected"
    assert all(row["trend"] == "INSUFFICIENT DATA" for row in result["timeframes"].values())
