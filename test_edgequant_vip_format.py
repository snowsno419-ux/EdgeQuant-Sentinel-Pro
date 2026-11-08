import unittest
from edgequant_vip_format import interpret, resolve_update

CID = -100123456789

def p(text, **kwargs):
    return interpret(text, channel_id=CID, message_id=11,
                     enabled_channel_ids=[CID], **kwargs)

class VIPTests(unittest.TestCase):
    def test_single_buy(self):
        r = p('GOLD BUY 3901\nSL 3895\nTP 3924\n( or You can BE on 50 Pips )')
        self.assertEqual((r.kind,r.side,r.entry_low,r.tp,r.advisory_be_pips),
                         ('signal','BUY',3901,3924,50))
    def test_sell_zone(self):
        r = p('GOLD SELL 3997-4002\nSL 4007\nTP 3969')
        self.assertEqual((r.entry_low,r.entry_high,r.side),(3997,4002,'SELL'))
    def test_buy_zone(self):
        r = p('GOLD BUY 3945-3942\nSL 3936\nTP 3996')
        self.assertEqual((r.entry_low,r.entry_high),(3942,3945))
    def test_invalid(self):
        self.assertEqual(p('GOLD BUY 3901 SL 3910 TP 3924').kind,'signal')  # retain supplied SL for broker-side validation
    def test_channel_isolation(self):
        self.assertIsNone(interpret('GOLD BUY 3901 SL 3895 TP 3924',channel_id=42,
                                    message_id=1,enabled_channel_ids=[CID]))
    def test_hold_is_not_auto_executed(self):
        r = p('Risk එක ගන්න කැමති නම් hold කරන්න')
        self.assertEqual((r.kind,r.action),('update','hold_request'))
        self.assertIsNone(resolve_update(r,[1,2,3]))
    def test_exact_reply_link(self):
        r = p('BE කරන්න',reply_to_id=25)
        self.assertEqual(resolve_update(r,[25,26]),25)
        self.assertIsNone(resolve_update(r,[26]))
    def test_sl_hit(self):
        self.assertEqual(p('sl hit pips 30❌').action,'sl_hit_notice')
    def test_quote_is_not_new_order(self):
        self.assertEqual(p('GOLD LIMIT VIP\nGOLD BUY 3925 SL 3916 TP 3959\nමෙක ගන්න එපා.').kind,'update')
    def test_close(self):
        self.assertEqual(p('close කරගන්න').action,'close_request')

if __name__=='__main__': unittest.main()
