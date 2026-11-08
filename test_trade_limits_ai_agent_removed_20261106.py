"""Offline regression tests. No Telegram, MT5, or network connections."""
import unittest
from pathlib import Path
import edgequant_auto as E
import edgequant_desktop as D


class RetiredAgentAndTradeLimits(unittest.TestCase):
    def test_agent_disabled(self):
        self.assertTrue(E.AI_AGENT_FEATURE_REMOVED)
        self.assertFalse(E.AGENT_ENABLED)
        self.assertFalse(hasattr(D.EdgeQuantApp, '_build_agent'))
        self.assertFalse(hasattr(D.EdgeQuantApp, 'agent_apply'))
        self.assertNotIn('tab_ag', Path(D.__file__).read_text(encoding='utf8'))
        self.assertNotIn('/agent     -', E.COMMANDS_HELP)

    def test_legacy_saved_preference_cannot_reenable_agent(self):
        original = E.AGENT_ENABLED
        try:
            E.apply_desktop_settings({'AGENT_ENABLED': True}, {'AGENT_ENABLED': 'bool'})
            self.assertFalse(E.AGENT_ENABLED)
        finally:
            E.AGENT_ENABLED = original

    def test_ui_lists_three_trade_caps_once(self):
        names = [row[0] for row in D.EdgeQuantApp.all_scalars()]
        for key in ('MAX_OPEN_ORDERS','MAX_TRADES_PER_SYMBOL','MAX_PENDING_PER_SYMBOL'):
            self.assertEqual(names.count(key), 1)
        for key in ('AGENT_ENABLED','AGENT_STYLE','AGENT_BUNDLE_S'):
            self.assertNotIn(key, names)
        source = Path(D.__file__).read_text(encoding='utf8')
        self.assertIn('section("MAX OPEN TRADES / ORDERS")',source)
        self.assertIn('limit < 0 or limit > 100000',source)

    def test_editable_caps_from_saved_client_settings(self):
        names=('MAX_OPEN_ORDERS','MAX_TRADES_PER_SYMBOL','MAX_PENDING_PER_SYMBOL')
        keep={k:getattr(E,k) for k in names}
        try:
            E.apply_desktop_settings({names[0]: 100,names[1]: 50,names[2]: 80},
                                     {k:'int' for k in names})
            self.assertEqual(tuple(getattr(E,n) for n in names),(100,50,80))
            E.apply_desktop_settings({n: 0 for n in names}, {n:'int' for n in names})
            self.assertEqual(tuple(getattr(E,n) for n in names),(0,0,0))
        finally:
            for name,value in keep.items(): setattr(E,name,value)

    def test_symbol_live_cap_is_adjustable(self):
        count_fn=E.symbol_live_count
        pend_fn=E.symbol_pending_count
        old=E.MAX_TRADES_PER_SYMBOL
        try:
            E.symbol_live_count=lambda symbol='': 12
            E.symbol_pending_count=lambda symbol='': 0
            E.MAX_TRADES_PER_SYMBOL=10
            self.assertFalse(E.symbol_cap_guard('XAUUSD')[0])
            E.MAX_TRADES_PER_SYMBOL=20
            self.assertTrue(E.symbol_cap_guard('XAUUSD')[0])
            E.MAX_TRADES_PER_SYMBOL=0
            self.assertTrue(E.symbol_cap_guard('XAUUSD')[0])
        finally:
            E.MAX_TRADES_PER_SYMBOL=old
            E.symbol_live_count=count_fn
            E.symbol_pending_count=pend_fn

    def test_other_management_controls_kept(self):
        names={row[0] for row in D.EdgeQuantApp.all_scalars()}
        self.assertTrue({'AUTO_BE_ENABLED','TRAILING_STOP','BE_LADDER_PIPS'} <= names)
        self.assertIn('if not AI_AGENT_FEATURE_REMOVED and AGENT_ENABLED and not DRY_RUN:',
                      Path(E.__file__).read_text(encoding='utf8'))

if __name__=='__main__':
    unittest.main()
