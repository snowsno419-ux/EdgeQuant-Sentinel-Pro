"""Regression tests: duplicate signals cannot create another two-layer pair."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from concurrent.futures import ThreadPoolExecutor

from edgequant_duplicate_guard import claim_plan, finalize_claims, identity_key


def pair(entry=4000.0, sl=3990.0, tp=4020.0, side='BUY', target1=4005.0):
    offset = 0.99 if side == 'BUY' else -0.90
    adjusted = round(entry + offset, 2)
    return [{'kind': 'PENDING', 'type': side + '_LIMIT', 'direct_limit': True,
             'src_price': entry, 'price': adjusted, 'sl': sl,
             'tp': target1 if layer == 1 else tp, 'layer': layer}
            for layer in (1, 2)]


class FakeMT5:
    def __init__(self, orders=None, positions=None):
        self.orders = [] if orders is None else orders
        self.positions = [] if positions is None else positions
    def orders_get(self, symbol=None):
        return self.orders
    def positions_get(self, symbol=None):
        return self.positions


class SignalContentDedupTests(unittest.TestCase):
    def claim(self, plan, folder, account=123, server='Demo-1', symbol='XAUUSDm',
              side='BUY', api=None, broker='MAIN'):
        return claim_plan(plan, login=account, server=server, broker=broker,
                          symbol=symbol, direction=side, mt5_api=api, magic=88001,
                          folder=folder)

    def test_same_entry_sl_tp_different_message_blocks_both_layers(self):
        with TemporaryDirectory() as folder:
            p1 = pair()
            eligible, dup, receipts, error = self.claim(p1, folder)
            self.assertEqual((len(eligible), dup, error), (2, 0, ''))
            self.assertEqual(len(receipts), 1)
            for row in eligible:
                row.update(status='pending', ticket=101 + row['layer'])
            finalize_claims(receipts)
            p2 = pair(target1=4010.0)  # changed user L1 quick TP is not a new signal
            eligible2, dup2, _, error2 = self.claim(p2, folder)
            self.assertEqual((len(eligible2), dup2, error2), (0, 1, ''))
            self.assertEqual([x['status'] for x in p2], ['duplicate', 'duplicate'])
            self.assertEqual(len(list(Path(folder).glob('*.json'))), 1)
            receipt = json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertEqual(receipt['state'], 'placed')
            self.assertEqual(receipt['tickets'], [102, 103])

    def test_repeated_price_within_one_message_is_deduplicated(self):
        with TemporaryDirectory() as folder:
            plan = pair(4000) + pair(4000)
            eligible, duplicates, claims, error = self.claim(plan, folder)
            self.assertEqual((len(eligible), duplicates, len(claims), error), (2, 1, 1, ''))
            self.assertEqual([x['status'] for x in plan[2:]], ['duplicate', 'duplicate'])

    def test_partial_entry_range_only_places_new_pair(self):
        with TemporaryDirectory() as folder:
            self.claim(pair(4000), folder)
            mixed = pair(4000) + pair(4010, sl=3990, tp=4020)
            eligible, duplicates, claims, error = self.claim(mixed, folder)
            self.assertEqual((len(eligible), duplicates, len(claims), error), (2, 1, 1, ''))
            self.assertEqual([x['src_price'] for x in eligible], [4010, 4010])

    def test_different_sl_tp_side_and_account_are_distinct(self):
        with TemporaryDirectory() as folder:
            self.claim(pair(), folder)
            self.assertEqual(len(self.claim(pair(sl=3980), folder)[0]), 2)
            self.assertEqual(len(self.claim(pair(tp=4030), folder)[0]), 2)
            self.assertEqual(len(self.claim(pair(side='SELL', sl=4010, tp=3980), folder, side='SELL')[0]), 2)
            self.assertEqual(len(self.claim(pair(), folder, account=124)[0]), 2)
            self.assertEqual(len(self.claim(pair(), folder, server='Demo-2')[0]), 2)

    def test_symbol_alias_and_broker_label_do_not_bypass_same_account(self):
        with TemporaryDirectory() as folder:
            self.claim(pair(), folder, symbol='XAUUSDm', broker='MAIN')
            eligible, duplicates, _, error = self.claim(pair(), folder, symbol='XAUUSD', broker='ICMARKETS')
            self.assertEqual((len(eligible), duplicates, error), (0, 1, ''))

    def test_exclusive_claim_survives_restart_and_uncertain_result(self):
        with TemporaryDirectory() as folder:
            self.claim(pair(), folder)
            eligible, duplicates, _, error = self.claim(pair(), folder)
            self.assertEqual((len(eligible), duplicates, error), (0, 1, ''))
            item = next(Path(folder).glob('*.json'))
            self.assertEqual(json.loads(item.read_text())['state'], 'claimed_before_submission')

    def test_mt5_live_pending_from_old_version_is_detected(self):
        with TemporaryDirectory() as folder:
            order = SimpleNamespace(magic=88001, price_open=4000.99, sl=3990.0, tp=4020.0)
            p = pair()
            eligible, dup, claims, error = self.claim(p, folder, api=FakeMT5(orders=[order]))
            self.assertEqual((len(eligible), dup, claims, error), (0, 1, [], ''))
            self.assertFalse(list(Path(folder).glob('*.json')))
            other = SimpleNamespace(magic=9, price_open=4000.99, sl=3990.0, tp=4020.0)
            self.assertEqual(len(self.claim(pair(), folder, api=FakeMT5(orders=[other]))[0]), 2)

    def test_unavailable_mt5_query_fails_closed(self):
        with TemporaryDirectory() as folder:
            api = FakeMT5()
            api.orders = None
            eligible, dup, claims, error = self.claim(pair(), folder, api=api)
            self.assertEqual(eligible, [])
            self.assertIn('fails', error.lower().replace('failed', 'fails'))
            self.assertEqual(claims, [])

    def test_invalid_account_or_invalid_pair_does_not_send(self):
        with TemporaryDirectory() as folder:
            plan = pair()
            eligible, _, _, error = self.claim(plan, folder, account=0)
            self.assertEqual(eligible, [])
            self.assertIn('unverified', error)
            plan2 = pair()
            plan2[1]['sl'] = 3989
            eligible2, _, _, error2 = self.claim(plan2, folder)
            self.assertEqual(eligible2, [])
            self.assertIn('mismatch', error2)

    def test_simultaneous_sources_race_only_one_receipt_wins(self):
        with TemporaryDirectory() as folder:
            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(lambda _: self.claim(pair(), folder), range(8)))
            self.assertEqual(sum(len(item[0]) == 2 for item in outcomes), 1)
            self.assertEqual(sum(item[1] == 1 for item in outcomes), 7)
            self.assertEqual(len(list(Path(folder).glob('*.json'))), 1)

    def test_no_deletion_on_explicit_rejection(self):
        with TemporaryDirectory() as folder:
            plan = pair()
            eligible, _, claims, error = self.claim(plan, folder)
            for row in eligible:
                row['status'] = 'rejected'
            finalize_claims(claims)
            self.assertEqual(self.claim(pair(), folder)[0], [])
            receipt = json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertEqual(receipt['state'], 'rejected_or_not_sent')


if __name__ == '__main__':
    unittest.main()
