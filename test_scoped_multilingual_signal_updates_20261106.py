"""Offline, broker-free exact Telegram signal edit tests."""
import unittest
from edgequant_signal_updates import parse_change, plan_changes, resolve_shorthand


def rows(message_id=55, chat_id=10, entry=4000.0, side='BUY', source='A GOLD CHANNEL',
         status='pending', broker='MAIN', signal='GOLD BUY 4000 SL 3950 TP 4100'):
    ep = round(entry + (0.99 if side == 'BUY' else -0.90), 2)
    return [dict(source=source, source_type='LIMIT', chat_id=chat_id, message_id=message_id,
                 ticket=200+i, broker=broker, status=status, direction=side, symbol='XAUUSDm',
                 sig_entry=entry, price=ep, open_price=ep, sl_now=3950 if side == 'BUY' else 4050,
                 tp_now=ep + (5 if side == 'BUY' else -5) if i == 0 else (4100 if side == 'BUY' else 3900),
                 pip=0.1, tag='quick50' if i == 0 else 'tp1', signal=signal)
            for i in range(2)]


def plan(txt, rows_input=None, *, original=False, reply=True):
    change, why = parse_change(txt, original_edit=original, is_reply=reply)
    assert change is not None, (txt, why)
    return plan_changes(change, rows_input or rows(), mode='original_edit' if original else 'followup',
                        source='A GOLD CHANNEL', chat_id=10, category='LIMIT',
                        original_message_id=55 if (reply or original) else None,
                        quick_pips=50, pip_size=0.1, digits=2)


class TestMultilingual(unittest.TestCase):
    def test_revised_complete_reply(self):
        a, _ = plan('GOLD BUY 4050 SL 4000 TP 4150')
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]['entry'], 4050.99)
        self.assertEqual(a[1]['tp'], 4150)

    def test_forex_digits_not_truncated(self):
        r = rows(entry=1.08500)
        for row in r:
            row['symbol'] = 'EURUSD'
            row['price'] = 1.08500
            row['open_price'] = 1.08500
            row['pip'] = 0.0001
            row['sl_now'] = 1.08000
            row['tp_now'] = 1.10000
        a, _ = plan('Move entry to 1.08612 and SL to 1.08123', r)
        self.assertEqual(a[0]['entry'], 1.08612)
        self.assertEqual(a[0]['tp'], 1.09112)

    def test_english_reply_exact_entry_and_sl(self):
        a, _ = plan('Move entry to 4050 and SL to 4000')
        self.assertEqual(len(a), 2)
        self.assertEqual({x['entry'] for x in a}, {4050.99})
        self.assertEqual({x['sl'] for x in a}, {4000})
        self.assertEqual(a[0]['tp'], 4055.99)
        self.assertIsNone(a[1]['tp'])

    def test_singlish(self):
        a, _ = plan('entry eka 4050ta ganna SL eka 4000ta tiyanna')
        self.assertEqual(len(a), 2)
        self.assertEqual(a[1]['sl'], 4000)

    def test_sinhala(self):
        a, _ = plan('මේකේ entry එක 4050ට ගන්න SL එක 4000ට තියන්න')
        self.assertEqual(a[0]['entry'], 4050.99)

    def test_sl_only_on_both_layers(self):
        a, _ = plan('SL එක 3980ට තියන්න')
        self.assertEqual(len(a), 2)
        self.assertTrue(all(x['entry'] is None and x['sl'] == 3980 and x['tp'] is None for x in a))

    def test_signal_tp_only_layer_two(self):
        a, _ = plan('change TP to 4150')
        self.assertEqual([x['ticket'] for x in a], [201])
        self.assertEqual(a[0]['tp'], 4150)

    def test_original_edit_full_signal(self):
        a, _ = plan('GOLD BUY 4050 SL 4000 TP 4150', original=True, reply=False)
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]['entry'], 4050.99)
        self.assertEqual(a[1]['tp'], 4150)

    def test_short_reply_relative_gold_price(self):
        signal_rows = rows(entry=3925)
        a, _ = plan('මේක ගන්න 24.25 ගනේ', signal_rows)
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]['entry'], 3925.24)  # 3924.25 source + original +0.99

    def test_short_original_edit_appended_comment(self):
        signal_rows = rows(entry=3923)
        a, _ = plan('GOLD BUY 3923 SL 3916 TP 3959 (or You can BE on 50 Pips) මේක ගන්න 24.25 ගනේ',
                    signal_rows, original=True, reply=False)
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]['entry'], 3925.24)

    def test_original_multi_entry_range(self):
        two = rows(entry=3997) + rows(entry=4002, message_id=55, broker='SECOND')
        for r in two:
            r['direction'] = 'SELL'
            r['sl_now'] = 4007
            r['tp_now'] = 3969
            r['price'] = r['sig_entry'] - 0.90
        a, _ = plan('GOLD SELL 4000-4005 SL 4010 TP 3960', two, original=True, reply=False)
        self.assertEqual(len(a), 4)
        self.assertEqual({x['entry'] for x in a}, {3999.1, 4004.1})

    def test_active_same_chat_but_different_original_id_is_scoped(self):
        r = rows() + rows(message_id=56, entry=4000, broker='MAIN2')
        a, _ = plan('Move entry to 4050 and SL to 4000', r)
        self.assertEqual({x['ticket'] for x in a}, {200, 201})

    def test_different_channel_is_scoped(self):
        r = rows() + rows(chat_id=30, entry=4000, source='Other Channel', broker='OTHER')
        a, _ = plan('Move entry to 4050 and SL to 4000', r)
        self.assertEqual(len(a), 2)

    def test_ambiguous_unthreaded_old_entry_blocked(self):
        r = rows() + rows(message_id=56, entry=4000, broker='OTHER')
        change, _ = parse_change('old entry 4000 new entry 4050', is_reply=False)
        a, why = plan_changes(change, r, mode='followup', source='A GOLD CHANNEL',
                              chat_id=10, category='LIMIT', original_message_id=None)
        self.assertFalse(a)
        self.assertIn('multiple original signals', why)

    def test_unthreaded_with_exact_old_entry_unique(self):
        change, _ = parse_change('from 4000 to 4050 SL 4000', is_reply=False)
        a, why = plan_changes(change, rows(), mode='followup', source='A GOLD CHANNEL',
                              chat_id=10, category='LIMIT')
        self.assertEqual(len(a), 2, why)

    def test_prohibited_unclear_shorthand_without_reply(self):
        c, why = parse_change('මේක ගන්න 24.25 ගනේ', is_reply=False)
        self.assertIsNone(c)

    def test_outcome_advisory_ignored(self):
        for x in ('GOLD BUY 4000 SL 3950 TP 4100 SL HIT',
                  'GOLD BUY 4000 SL 3950 TP 4100 (or You can BE on 50 Pips)'):
            if 'HIT' in x:
                c, _ = parse_change(x, original_edit=True)
                self.assertIsNone(c)
            else:
                c, _ = parse_change(x, is_reply=True)
                self.assertIsNotNone(c)  # exact reply can carry full updated signal + advisory

    def test_no_numeric_update_is_not_trade_edit(self):
        c, _ = parse_change('aye buy ganna epa', is_reply=True)
        self.assertIsNone(c)

    def test_filled_position_sl_changes_not_entry(self):
        r = rows(status='open')
        a, why = plan('entry eka 4050ta ganna SL eka 4000ta tiyanna', r)
        self.assertEqual(len(a), 2, why)
        self.assertTrue(all(x['entry'] is None and x['sl'] == 4000 for x in a))

    def test_be_protected_sl_not_weakened(self):
        r = rows(status='open')
        for x in r:
            x['sl_now'] = 4010
        a, why = plan('change SL to 3950', r)
        self.assertFalse(a)

    def test_one_original_msg_two_layers_and_two_brokers(self):
        r = rows() + rows(broker='SECOND')
        a, _ = plan('Move entry to 4050 and SL to 4000', r)
        self.assertEqual(len(a), 4)

    def test_selling_spread_offset(self):
        r = rows(entry=4023, side='SELL')
        a, _ = plan('move entry to 4018 and SL to 4030', r)
        self.assertEqual(a[0]['entry'], 4017.1)
        self.assertEqual(a[0]['tp'], 4012.1)
        self.assertEqual(a[1]['tp'], None)

    def test_price_shortcut_limit_rejects_far(self):
        self.assertIsNone(resolve_shorthand(24.25, 4070, 'XAUUSD'))
        self.assertEqual(resolve_shorthand(24.25, 3925, 'XAUUSD'), 3924.25)


if __name__ == '__main__':
    unittest.main()
