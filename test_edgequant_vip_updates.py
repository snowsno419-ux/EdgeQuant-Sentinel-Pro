import unittest
from edgequant_vip_format import interpret
from edgequant_vip_updates import plan_update
CID = -100123456789

def parse(text, reply=None):
    return interpret(text, channel_id=CID, message_id=88, reply_to_id=reply,
                     enabled_channel_ids=[CID])

def record(mid=11, ticket=1001, status='open', chat=CID, broker='DEMO'):
    return dict(chat_id=chat, message_id=mid, ticket=ticket, status=status,
                source='GOLD LIMIT VIP', source_type='LIMIT', broker=broker)

class VIPUpdateTests(unittest.TestCase):
    def test_entry_change_pending_only(self):
        plan, reason = plan_update(parse('Change entry to 3912', 11),
                                   [record(status='pending'), record(ticket=1002, status='open')])
        self.assertEqual(reason, '')
        self.assertEqual(plan.action, 'entry_update_request')
        self.assertEqual(plan.new_entry, 3912)
        self.assertEqual(plan.tickets_by_broker, {'DEMO': [1001]})

    def test_entry_change_no_explicit_price_is_blocked(self):
        plan, reason = plan_update(parse('entry වෙනස් කරන්න', 11), [record(status='pending')])
        self.assertIsNone(plan)

    def test_entry_change_without_reply_is_blocked(self):
        plan, reason = plan_update(parse('Entry 3912'), [record(status='pending')])
        self.assertIsNone(plan)

    def test_be_exact_reply_only(self):
        plan, why = plan_update(parse('BE කරන්න',11), [record()])
        self.assertEqual(plan.tickets_by_broker, {'DEMO':[1001]})
        self.assertEqual(plan.action, 'be_request')
    def test_no_reply_never_matches(self):
        self.assertIsNone(plan_update(parse('BE කරන්න'), [record()])[0])
    def test_wrong_channel_no_match(self):
        self.assertIsNone(plan_update(parse('BE කරන්න',11), [record(chat=-1009)])[0])
    def test_hold_does_not_modify(self):
        self.assertIsNone(plan_update(parse('Risk එක ගන්න කැමති නම් hold කරන්න',11),[record()])[0])
    def test_sl_hit_does_not_modify(self):
        self.assertIsNone(plan_update(parse('SL hit pips 30',11),[record()])[0])
    def test_cancel_pending_only(self):
        plan, _ = plan_update(parse('do not enter',11),[record(status='open'),record(ticket=1002,status='pending')])
        self.assertEqual(plan.tickets_by_broker,{'DEMO':[1002]})
    def test_close_open_only(self):
        plan, _ = plan_update(parse('close කරගන්න',11),[record(status='open'),record(ticket=1002,status='pending')])
        self.assertEqual(plan.tickets_by_broker,{'DEMO':[1001]})
    def test_advisory_not_immediate_be(self):
        self.assertEqual(parse('( or You can BE on 50 Pips )').action,'ignore')
    def test_quoted_signal_not_new_order(self):
        r=parse('GOLD LIMIT VIP\nGOLD BUY 3925 SL 3916 TP 3959 (or You can BE on 50 Pips)\nමෙක ගන්න එපා.',11)
        self.assertEqual((r.kind,r.action),('update','cancel_entry_request'))
    def test_unlinked_update_does_not_guess_by_symbol(self):
        self.assertIsNone(plan_update(parse('GOLD BUY 3901 BE කරන්න',12),[record(mid=11)])[0])

if __name__=='__main__': unittest.main()
