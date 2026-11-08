import unittest
from types import SimpleNamespace as O
from edgequant_limit_daily import classify_with_states
class DailyLimitTests(unittest.TestCase):
    def test_activation_requires_deal(self):
        orders=[O(ticket=1,type=2,magic=42,state=4,volume_initial=.02,volume_current=0,symbol='XAUUSD',price_open=3000,time_setup=100),O(ticket=2,type=3,magic=42,state=2,volume_initial=.02,volume_current=.02,symbol='XAUUSD',price_open=3010,time_setup=100),O(ticket=3,type=2,magic=42,state=4,volume_initial=.02,volume_current=0,symbol='XAUUSD',price_open=2990,time_setup=100)]
        deals=[O(order=1,entry=0)]
        r=classify_with_states(orders,deals,{2,3},magic=42)
        self.assertEqual([x['ticket'] for x in r['activated']],[1])
        self.assertEqual([x['ticket'] for x in r['untriggered']],[2])
        self.assertEqual([x['ticket'] for x in r['unknown']],[3])
if __name__=='__main__': unittest.main()
