"""Offline regression suite; NEVER connects to Telegram or places MT5 orders."""
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
import edgequant_auto as E
from edgequant_vip_signal_edits import read_signal, plan_edited_original
from edgequant_vip_format import interpret
from edgequant_vip_updates import plan_update

CID=-100735579

def record(ticket, tag='quick50', broker='MAIN', message_id=101, entry=4000.0,
           status='pending', sl=3950.2, tp=None):
    return {'chat_id':CID,'message_id':message_id,'source':'GOLD LIMIT VIP',
            'source_type':'LIMIT','broker':broker,'ticket':ticket,'status':status,
            'tag':tag,'symbol':'XAUUSD','direction':'BUY','sig_entry':entry,
            'price':entry+0.99,'open_price':entry+0.99,
            'sl_now':sl, 'tp_now':tp if tp is not None else (4005.99 if tag.startswith('quick') else 4100),
            'signal':'GOLD BUY 4000 | SL 3950 | TP 4100'}

class VIPEntryAndEditTests(unittest.TestCase):
    def test_buy_stop_fallback_keeps_fixed_offset_and_two_layers(self):
        with patch.object(E, '_CUR_CHANNEL', ['GOLD LIMIT VIP']):
            sig=E.parse_signal('GOLD BUY 4064 SL 4055 TP 4099',default_order_type='LIMIT')
            plan=E.build_plan(sig,'LIMIT',E.Broker(stops_level=10),ask=4060.5,bid=4060.3,balance=1000)
        self.assertEqual(len(plan),2)
        self.assertEqual([r['kind'] for r in plan],['PENDING']*2)
        self.assertEqual([r['type'] for r in plan],['BUY_LIMIT']*2)
        self.assertEqual([r['price'] for r in plan],[4064.99]*2)
        self.assertEqual([r['tp'] for r in plan],[4069.99,4099])
        self.assertEqual([r['sl'] for r in plan],[4055.0]*2)

    def test_sell_stop_fallback_sl_and_layers(self):
        with patch.object(E, '_CUR_CHANNEL', ['GOLD LIMIT VIP']):
            sig=E.parse_signal('GOLD SELL 4125 SL 4134 TP 4090',default_order_type='LIMIT')
            plan=E.build_plan(sig,'LIMIT',E.Broker(stops_level=10),ask=4130.8,bid=4130.5,balance=1000)
        self.assertEqual(len(plan),2)
        self.assertEqual([r['type'] for r in plan],['SELL_LIMIT']*2)
        self.assertEqual([r['price'] for r in plan],[4124.1]*2)
        self.assertEqual([r['sl'] for r in plan],[4134.0]*2)
        self.assertEqual([r['tp'] for r in plan],[4119.1,4090])

    def test_valid_sell_limit_is_not_converted_to_stop(self):
        self.assertEqual(E.gold_vip_pending_type('SELL',4104.10,4100.2,4100,0.12)[0],'SELL_LIMIT')

    def test_min_distance_zone_blocks_both_types(self):
        self.assertIsNone(E.gold_vip_pending_type('BUY',4064.99,4065,4064.8,0.12)[0])
        self.assertIsNone(E.gold_vip_pending_type('SELL',4100.05,4100.2,4100,0.12)[0])

    def test_buy_range_has_four_orders_two_per_entry(self):
        with patch.object(E, '_CUR_CHANNEL', ['GOLD LIMIT VIP']):
            sig=E.parse_signal('GOLD BUY 3942-3945 SL 3936 TP 3996',default_order_type='LIMIT')
            plan=E.build_plan(sig,'LIMIT',E.Broker(),ask=3950,bid=3949.8,balance=1000)
        self.assertEqual(len(plan),4)
        self.assertEqual([r['price'] for r in plan],[3942.99]*2+[3945.99]*2)
        self.assertEqual([r['tp'] for r in plan],[3947.99,3996,3950.99,3996])

    def test_owner_auto_be_off_rejects_auto_layer_gate(self):
        with patch.object(E,'AUTO_BE_ENABLED',False),patch.object(E,'AUTO_BE_LAYER_TICKETS',{('MAIN',12):2}):
            self.assertFalse(E.auto_be_ticket_allowed(12,'MAIN'))
        with patch.object(E,'AUTO_BE_ENABLED',True),patch.object(E,'AUTO_BE_LAYER_TICKETS',{('MAIN',12):2}):
            self.assertTrue(E.auto_be_ticket_allowed(12,'MAIN'))

    def test_full_original_tp_edit_only_updates_l2_on_two_brokers(self):
        rows=[record(1),record(2,tag='tp1'),record(1,broker='EXNESS'),record(2,'tp1',broker='EXNESS')]
        edits,reason=plan_edited_original('GOLD BUY 4000 SL 3950 TP 4150',CID,101,rows)
        self.assertEqual(len(edits),2)
        self.assertEqual({e['broker'] for e in edits},{'MAIN','EXNESS'})
        self.assertEqual({e['ticket'] for e in edits},{2})
        self.assertEqual({e['tp'] for e in edits},{4150})
        self.assertTrue(all(e['sl'] is None and e['entry'] is None for e in edits))

    def test_full_original_sl_edit_updates_both_layers_and_brokers(self):
        rows=[record(1),record(2,tag='tp1'),record(1,broker='EXNESS'),record(2,'tp1',broker='EXNESS')]
        edits,_=plan_edited_original('GOLD BUY 4000 SL 3960 TP 4100',CID,101,rows)
        self.assertEqual(len(edits),4)
        self.assertEqual({e['sl'] for e in edits},{3960.2})
        self.assertTrue(all(e['tp'] is None for e in edits))

    def test_pending_entry_edit_preserves_two_layers_and_quick_tp_recalculated(self):
        rows=[record(1),record(2,tag='tp1')]
        edits,_=plan_edited_original('GOLD BUY 4001 SL 3950 TP 4100',CID,101,rows)
        self.assertEqual(len(edits),2)
        self.assertEqual([e['entry'] for e in edits],[4001.99]*2)
        self.assertEqual([e['tp'] for e in edits],[4006.99,None])

    def test_filled_entry_cannot_be_modified(self):
        rows=[record(1,status='open'),record(2,tag='tp1',status='open')]
        edits,_=plan_edited_original('GOLD BUY 4001 SL 3950 TP 4150',CID,101,rows)
        self.assertTrue(edits)
        self.assertTrue(all(e['entry'] is None for e in edits))
        self.assertEqual(len(edits),1)
        self.assertEqual(edits[0]['ticket'],2)
        self.assertEqual(edits[0]['tp'],4150)

    def test_no_cross_message_update_even_same_symbol_or_ticket(self):
        rows=[record(1,message_id=102),record(2,'tp1',message_id=102)]
        edits,why=plan_edited_original('GOLD BUY 4000 SL 3950 TP 4150',CID,101,rows)
        self.assertFalse(edits)
        self.assertIn('no journaled',why)

    def test_result_sl_hit_edit_does_not_modify(self):
        rows=[record(1),record(2,'tp1')]
        edits,_=plan_edited_original('GOLD BUY 4000 SL 3950 TP 4100\nsl hit pips 30',CID,101,rows)
        self.assertFalse(edits)

    def test_invalid_or_ambiguous_range_edit_rejected(self):
        rows=[record(1),record(2,'tp1')]
        edits,_=plan_edited_original('GOLD BUY 4000-4001 SL 3950 TP 4100',CID,101,rows)
        self.assertFalse(edits)

    def test_tp_only_edit_does_not_undo_existing_broker_profit_lock(self):
        r1=record(1,sl=4001.50)
        r2=record(2,'tp1',sl=4001.50)
        edits,why=plan_edited_original('GOLD BUY 4000 SL 3950 TP 4150',CID,101,[r1,r2])
        self.assertEqual(len(edits),1)
        self.assertEqual(edits[0]['ticket'],2)
        self.assertIsNone(edits[0]['sl'])
        self.assertEqual(edits[0]['tp'],4150)

    def test_singlish_replied_entry_modification_requires_original_message(self):
        from edgequant_vip_format import interpret
        for text in ('entry eka 4001ta wenas karanna', 'entry 4001ට වෙනස් කරන්න',
                     'Buy 4001ta wenas kranna'):
            with self.subTest(text=text):
                it=interpret(text,channel_id=CID,message_id=102,reply_to_id=101,enabled_channel_ids=[CID])
                self.assertEqual(it.action,'entry_update_request')
                self.assertEqual(it.new_entry,4001)
                plan,why=plan_update(it,[record(1),record(2,'tp1')])
                self.assertEqual(plan.tickets_by_broker,{'MAIN':[1,2]})

    def test_runtime_original_edit_idempotence_and_exact_broker_tickets(self):
        rows=[record(1),record(2,'tp1'),record(1,broker='EXNESS'),record(2,'tp1',broker='EXNESS')]
        calls=[]
        def edit(ticket,**kwargs):
            calls.append((kwargs['broker'],ticket,kwargs.get('tp'),kwargs.get('sl')))
            return {'ok':True,'message':'offline test'}
        with TemporaryDirectory() as td, patch.object(E,'TRADES',rows),patch.object(E,'HERE',Path(td)), \
             patch.object(E,'DRY_RUN',False),patch.object(E,'HAVE_MT5',True), \
             patch.object(E,'mt5_ready',return_value=True),patch.object(E,'mt5_edit_ticket',side_effect=edit), \
             patch.object(E,'signal_audit',return_value=None):
            self.assertTrue(E.apply_gold_vip_original_edit('GOLD BUY 4000 SL 3950 TP 4150',
                                                             'GOLD LIMIT VIP',CID,101,'LIMIT'))
            self.assertEqual(calls,[('MAIN',2,4150,None),('EXNESS',2,4150,None)])
            self.assertTrue(E.apply_gold_vip_original_edit('GOLD BUY 4000 SL 3950 TP 4150',
                                                             'GOLD LIMIT VIP',CID,101,'LIMIT'))
            self.assertEqual(len(calls),2, 'duplicate MessageEdited must not resend MT5 mutations')

    def test_sell_original_full_edit_preserves_sell_sl_offset(self):
        r={'chat_id':CID, 'message_id':71, 'ticket':9, 'broker':'MAIN',
           'source':'GOLD LIMIT VIP','source_type':'LIMIT','status':'pending',
           'tag':'tp1','direction':'SELL','symbol':'XAUUSD', 'sig_entry':4105.0,
           'sl_now':4110-0.20, 'tp_now':4080, 'open_price':4105-0.90,
           'signal':'GOLD SELL 4105 | SL 4110 | TP 4080'}
        actions,why=plan_edited_original('GOLD SELL 4105 SL 4112 TP 4070',CID,71,[r])
        self.assertEqual(len(actions),1,why)
        self.assertEqual(actions[0]['sl'],4111.80)
        self.assertEqual(actions[0]['tp'],4070)

    def test_mixed_language_reply_tp_sl(self):
        orig=[record(1),record(2,'tp1')]
        for text,action,value in [('TP eka 4150ta wenas kranna','tp_update_request',4150),
                                  ('TP eka 4150ට වෙනස් කරන්න','tp_update_request',4150),
                                  ('SL eka 3999ta wenas karanna','sl_update_request',3999),
                                  ('SL 3999 වෙනස් කරන්න','sl_update_request',3999)]:
            with self.subTest(text=text):
                it=interpret(text,channel_id=CID,message_id=102,reply_to_id=101,enabled_channel_ids=[CID])
                self.assertEqual(it.action,action)
                p,reason=plan_update(it,orig)
                self.assertIsNotNone(p,reason)
                self.assertEqual(p.new_tp if action.startswith('tp') else p.new_sl,value)
        it=interpret('TP eka 4150ta wenas kranna',channel_id=CID,message_id=102,enabled_channel_ids=[CID])
        self.assertIsNone(plan_update(it,orig)[0])

if __name__=='__main__':
    unittest.main()
