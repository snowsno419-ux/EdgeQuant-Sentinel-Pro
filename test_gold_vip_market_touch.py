"""Offline regression suite for persistent GOLD LIMIT VIP first-touch fallback."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import edgequant_auto as E
import edgequant_vip_market_touch as W
from edgequant_vip_format import interpret

CID = -100990001


def orders(entry=4064.99, source=4064.0, side='BUY'):
    tp1 = round(entry + (5 if side == 'BUY' else -5),2)
    tp2 = 4100 if side == 'BUY' else 4000
    sl = 4050.2 if side == 'BUY' else 4080.8
    return [{'kind':'WATCH_MARKET','type':side,'price':entry, 'sl':sl,
             'tp':tp, 'tag':tag,'lot':0.01,'src_price':source,
             'status':'watch_waiting'}
            for tp,tag in ((tp1,'quick50'),(tp2,'tp1'))]


def record(entry=4064.99, src=4064.0, broker='MAIN', mid=101, side='BUY', levels=None):
    return {'source':'GOLD LIMIT VIP', 'category':'LIMIT','chat_id':CID,
            'message_id':mid,'broker':broker,'login':123,'server':'Demo-Server',
            'symbol':'XAUUSD','direction':side,'src_price':src,'entry':entry,
            'digits':2,'original_levels':levels or [src], 'orders':orders(entry,src,side)}


class TouchPlanTests(unittest.TestCase):
    def test_buy_near_market_arms_two_layers_without_immediate_deal(self):
        sig=E.parse_signal('GOLD BUY 4064 SL 4055 TP 4100', default_order_type='LIMIT')
        with patch.object(E,'_CUR_CHANNEL',['GOLD LIMIT VIP']):
            p=E.build_plan(sig,'LIMIT',E.Broker(stops_level=20),4065.0,4064.8)
        self.assertEqual([r['kind'] for r in p], ['PENDING']*2)
        self.assertTrue(all(r.get('status') != 'watch_waiting' for r in p))
        self.assertEqual([r['type'] for r in p], ['BUY_LIMIT']*2)
        self.assertEqual([r['price'] for r in p], [4064.99]*2)
        self.assertEqual([r['tp'] for r in p], [4069.99,4100])
        self.assertEqual([r['sl'] for r in p], [4055.0]*2)

    def test_sell_near_market_arms_two_layers(self):
        sig=E.parse_signal('GOLD SELL 4125 SL 4135 TP 4100',default_order_type='LIMIT')
        with patch.object(E,'_CUR_CHANNEL',['GOLD LIMIT VIP']):
            p=E.build_plan(sig,'LIMIT',E.Broker(stops_level=20),4124.25,4124.15)
        self.assertEqual([r['kind'] for r in p], ['PENDING']*2)
        self.assertEqual([r['type'] for r in p],['SELL_LIMIT']*2)
        self.assertEqual([r['price'] for r in p],[4124.1]*2)
        self.assertEqual([r['tp'] for r in p],[4119.1,4100])

    def test_invalid_sl_not_armed(self):
        sig=E.parse_signal('GOLD BUY 4064 SL 4070 TP 4100',default_order_type='LIMIT')
        with patch.object(E,'_CUR_CHANNEL',['GOLD LIMIT VIP']):
            p=E.build_plan(sig,'LIMIT',E.Broker(stops_level=20),4065,4064.8)
        self.assertFalse(any(r['kind']=='WATCH_MARKET' for r in p))

    def test_range_keeps_four_layers_when_one_level_needs_market_watch(self):
        sig=E.parse_signal('GOLD BUY 4064-4068 SL 4050 TP 4120',default_order_type='LIMIT')
        with patch.object(E,'_CUR_CHANNEL',['GOLD LIMIT VIP']):
            p=E.build_plan(sig,'LIMIT',E.Broker(stops_level=20),4065,4064.8)
        self.assertEqual(len(p),4)
        self.assertEqual([r['kind'] for r in p].count('WATCH_MARKET'),0)
        self.assertEqual([r['kind'] for r in p].count('PENDING'),4)

    def test_only_buy_ask_sell_bid_touch_and_no_price_chase(self):
        self.assertTrue(W.at_first_touch('BUY',4064.99,4064.8,4065.03,0.1))
        self.assertFalse(W.at_first_touch('BUY',4064.99,4064.8,4065.5,0.1))
        self.assertTrue(W.at_first_touch('SELL',4124.10,4124.13,4124.30,0.1))
        self.assertFalse(W.at_first_touch('SELL',4124.10,4123.8,4124.1,0.1))
        self.assertFalse(W.at_first_touch('BUY',4064.99,4065.5,4065.0,0.1))

    def test_market_pair_requires_both_protected_targets(self):
        pair=orders()
        self.assertTrue(W.protected_pair_at_quote(pair,'BUY',4064.8,4064.99,0.1,0.01)[0])
        pair[1]['sl']=4065.3
        self.assertFalse(W.protected_pair_at_quote(pair,'BUY',4064.8,4064.99,0.1,0.01)[0])


class WatchStorageTests(unittest.TestCase):
    def test_durable_exact_identity_cannot_rearm_even_after_claim(self):
        with tempfile.TemporaryDirectory() as td:
            r=record()
            path=W.store_new(td,r)
            self.assertTrue(path.exists())
            self.assertEqual(W.load(path)['status'],'waiting')
            self.assertIsNone(W.store_new(td,r))
            self.assertTrue(W.claim(path))
            self.assertFalse(W.claim(path))
            self.assertIsNone(W.store_new(td,r))

    def test_separate_brokers_and_entries_have_independent_watch(self):
        with tempfile.TemporaryDirectory() as td:
            a=W.store_new(td,record())
            b=W.store_new(td,record(broker='EXNESS'))
            c=W.store_new(td,record(src=4062,entry=4062.99))
            self.assertEqual(len({a,b,c}),3)
            self.assertEqual(len(list(W.active(td,chat_id=CID,message_id=101))),3)
            self.assertTrue(W.claim(a))
            self.assertTrue(W.claim(b))

    def test_original_edit_updates_only_source_and_tp_layer2(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E,'_user_brokers_folder',return_value=Path(td)):
            folder=E.vip_market_watch_folder()
            path=W.store_new(folder,record())
            other=W.store_new(folder,record(mid=102))
            result=E.vip_market_watch_rewrite_original('GOLD BUY 4064 SL 4055 TP 4150',CID,101)
            self.assertTrue(result)
            self.assertEqual(W.load(path)['orders'][1]['tp'],4150)
            self.assertEqual(W.load(path)['orders'][0]['tp'],4069.99)
            self.assertEqual(W.load(other)['orders'][1]['tp'],4100)

    def test_exact_reply_cancels_unfilled_watch_not_another_signal(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E,'_user_brokers_folder',return_value=Path(td)):
            folder=E.vip_market_watch_folder()
            p=W.store_new(folder,record())
            other=W.store_new(folder,record(mid=102))
            reply=interpret("Don't enter",channel_id=CID,message_id=200,
                            reply_to_id=101,enabled_channel_ids=(CID,))
            self.assertEqual(E.vip_market_watch_apply_reply(reply),1)
            self.assertEqual(W.load(p)['status'],'cancelled_by_reply')
            self.assertEqual(W.load(other)['status'],'waiting')

    def test_reply_tp_update_keeps_quick_50_pip_target(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E,'_user_brokers_folder',return_value=Path(td)):
            folder=E.vip_market_watch_folder()
            p=W.store_new(folder,record())
            reply=interpret('TP eka 4150ta wenas kranna',channel_id=CID,
                            message_id=201,reply_to_id=101,enabled_channel_ids=(CID,))
            self.assertEqual(E.vip_market_watch_apply_reply(reply),1)
            self.assertEqual(W.load(p)['orders'][1]['tp'],4150)
            self.assertEqual(W.load(p)['orders'][0]['tp'],4069.99)
            self.assertEqual(E.vip_market_watch_apply_reply(reply),0)

    def test_virtual_wait_be_is_advisory_not_forced(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E,'_user_brokers_folder',return_value=Path(td)), patch.object(E,'AUTO_BE_ENABLED',False):
            folder=E.vip_market_watch_folder()
            p=W.store_new(folder,record())
            reply=interpret('BE karanna',channel_id=CID,message_id=202,
                            reply_to_id=101,enabled_channel_ids=(CID,))
            self.assertEqual(E.vip_market_watch_apply_reply(reply),0)
            self.assertEqual(W.load(p)['status'],'waiting')


class WatchEngineTests(unittest.TestCase):
    def test_main_broker_one_shot_two_market_orders(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/'gold_vip_market_touch'
            p=W.store_new(folder,record())
            spec=SimpleNamespace(point=0.01,trade_stops_level=0,trade_freeze_level=0,
                                 trade_tick_size=0.01,digits=2)
            tick=SimpleNamespace(bid=4064.82,ask=4064.99,time=time.time())
            api=SimpleNamespace(account_info=lambda:SimpleNamespace(login=123,server='Demo-Server'),
                                symbol_info=lambda sym:spec,symbol_info_tick=lambda sym:tick)
            sent=[]
            def fake_execute(plan,symbol,*args,**kwargs):
                self.assertEqual(symbol,'XAUUSD')
                self.assertEqual([o['kind'] for o in plan],['MARKET']*2)
                self.assertEqual([o['type'] for o in plan],['BUY']*2)
                self.assertEqual([o['price'] for o in plan],[4064.99]*2)
                for i,o in enumerate(plan):
                    o.update(status='open', ticket=100+i,fill_price=4064.99,
                             fill_ts=time.time())
                sent.append(1)
                return [100,101]
            patches=[patch.object(E,'_user_brokers_folder',return_value=Path(td)),
                     patch.object(E,'mt5',api),patch.object(E,'HAVE_MT5',True),
                     patch.object(E,'DRY_RUN',False),patch.object(E,'TRADE_JOURNAL',False),
                     patch.object(E,'AUTO_BE_ENABLED',False),
                     patch.object(E,'edgequant_external_stop_active',return_value=False),
                     patch.object(E,'stop_requested',return_value=False),
                     patch.object(E,'select_broker',return_value=True),
                     patch.object(E,'broker_is_on',return_value=True),
                     patch.object(E,'channel_is_on',return_value=True),
                     patch.object(E,'resolve_symbol',return_value='XAUUSD'),
                     patch.object(E,'can_trade_now',return_value=(True,'')),
                     patch.object(E,'extra_guards',return_value=(True,'')),
                     patch.object(E,'execute_plan',side_effect=fake_execute),
                     patch.object(E,'TRADES',[]), patch.object(E,'BROKER_TICKETS',{}),
                     patch.object(E,'AUTO_BE_LAYER_TICKETS',{}),
                     patch.object(E,'_CUR_CHANNEL',['old'])]
            try:
                for q in patches:q.start()
                self.assertEqual(E.vip_market_watch_tick_once(),1)
                self.assertEqual(W.load(p)['status'],'completed')
                self.assertEqual(W.load(p)['tickets'],[100,101])
                self.assertEqual(E.vip_market_watch_tick_once(),0)
                self.assertEqual(sent,[1])
            finally:
                for q in reversed(patches):q.stop()

    def test_off_broker_never_triggers_and_cancels_watch(self):
        with tempfile.TemporaryDirectory() as td:
            p=W.store_new(Path(td)/'gold_vip_market_touch',record())
            with patch.object(E,'_user_brokers_folder',return_value=Path(td)), \
                 patch.object(E,'HAVE_MT5',True),patch.object(E,'mt5',object()), \
                 patch.object(E,'DRY_RUN',False), \
                 patch.object(E,'stop_requested',return_value=False), \
                 patch.object(E,'edgequant_external_stop_active',return_value=False), \
                 patch.object(E,'broker_is_on',return_value=False), \
                 patch.object(E,'channel_is_on',return_value=True):
                self.assertEqual(E.vip_market_watch_tick_once(),0)
            self.assertEqual(W.load(p)['status'],'cancelled_off')


if __name__ == '__main__':
    unittest.main()

class DefiniteBrokerRejectionTests(unittest.TestCase):
    def _run_broker_reject(self, code):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            info=SimpleNamespace(point=0.01,trade_stops_level=0,trade_freeze_level=0,
                                 trade_tick_size=0.01,digits=2,filling_mode=1)
            tick=SimpleNamespace(bid=4069.8,ask=4070.0,time=time.time())
            mt=SimpleNamespace(symbol_info=lambda symbol:info,
                               symbol_info_tick=lambda symbol:tick,
                               account_info=lambda:SimpleNamespace(login=123,server='Demo-Server'),
                               TRADE_ACTION_PENDING=5,TRADE_ACTION_DEAL=1,
                               TRADE_RETCODE_DONE=10009, TRADE_RETCODE_PLACED=10008,
                               TRADE_RETCODE_DONE_PARTIAL=10010,
                               TRADE_RETCODE_INVALID_PRICE=10015,
                               TRADE_RETCODE_INVALID_STOPS=10016,
                               ORDER_TYPE_BUY_LIMIT=2,ORDER_TYPE_BUY_STOP=4,
                               ORDER_TIME_GTC=0,
                               last_error=lambda:('demo',0))
            plan=[{'kind':'PENDING','type':'BUY_LIMIT','price':4064.99,'sl':4055.2,
                   'tp':tp,'tag':tag,'lot':0.01,'src_price':4064.0}
                  for tp,tag in ((4069.99,'quick50'),(4100,'tp1'))]
            calls=[]
            def reject(req):
                calls.append(req.copy())
                return SimpleNamespace(retcode=code,comment='test rejected')
            with patch.object(E,'_user_brokers_folder',return_value=p), \
                 patch.object(E,'mt5',mt),patch.object(E,'HAVE_MT5',True), \
                 patch.object(E,'DRY_RUN',False), \
                 patch.object(E,'edgequant_external_stop_active',return_value=False), \
                 patch.object(E,'pick_filling',return_value=0), \
                 patch.object(E,'send_order',side_effect=reject), \
                 patch.object(E,'_CUR_CHANNEL',['GOLD LIMIT VIP']):
                out=E.execute_plan(plan,'XAUUSD',watch_context={
                    'source':'GOLD LIMIT VIP','broker':'MAIN',
                    'login':123,'server':'Demo-Server','chat_id':CID,
                    'message_id':12345,'entries':[4064]})
            existing=list(W.active(p/'gold_vip_market_touch'))
            return plan,out,existing,calls

    def test_broker_definite_10015_falls_back_to_watch(self):
        plan,tickets,watch,calls=self._run_broker_reject(10015)
        self.assertEqual(tickets,[])
        self.assertEqual(len(calls),4)  # broker definite reject -> existing comment-free retry
        self.assertEqual([r['status'] for r in plan], ['watch_waiting']*2)
        self.assertEqual([r['kind'] for r in plan], ['WATCH_MARKET']*2)
        self.assertEqual(len(watch),1)

    def test_broker_invalid_stops_never_triggers_market_fallback(self):
        plan,tickets,watch,calls=self._run_broker_reject(10016)
        self.assertEqual(tickets,[])
        self.assertEqual(len(watch),0)
        self.assertEqual([r['status'] for r in plan], ['rejected']*2)
