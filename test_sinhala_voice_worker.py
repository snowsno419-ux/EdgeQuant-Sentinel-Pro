"""Offline tests for dynamic Sinhala number/time normalization (no model needed)."""
import re
import unittest

import edgequant_sinhala_voice_worker as worker


class SinhalaVoiceTextTests(unittest.TestCase):
    def test_integer_words(self):
        self.assertEqual(worker.sinhala_integer_words(0), "බිංදුව")
        self.assertEqual(worker.sinhala_integer_words(18), "දහඅට")
        self.assertIn("දහස්", worker.sinhala_integer_words(1012))
        self.assertIn("විසි හය", worker.sinhala_integer_words(2026))

    def test_decimals_preserve_every_fraction_digit(self):
        text = worker.expand_dynamic_text("P&L 18.25 USD and 2.05 USD")
        self.assertIn("දශම දෙක පහ", text)
        self.assertIn("දෙක දශම බිංදුව පහ", text)
        self.assertNotRegex(text, r"\d")

    def test_currency_symbol_and_time_are_expanded(self):
        text = worker.expand_dynamic_text("XAUUSD at 14:05:09; balance 1,012.50 USD")
        self.assertIn("ගෝල්ඩ්", text)
        self.assertIn("පැය", text)
        self.assertIn("මිනිත්තු", text)
        self.assertIn("තත්පර", text)
        self.assertIn("ඇමරිකානු ඩොලර්", text)
        self.assertNotRegex(text, r"\d")

    def test_percent_and_trading_acronyms_are_sinhala(self):
        text = worker.expand_dynamic_text("TP 50%; SL 2.50 USD; BE; MT5")
        for token in ("ටී පී", "සියයට", "එස් එල්", "බී ඊ", "එම් ටී පහ"):
            self.assertIn(token, text)
        self.assertNotRegex(text, r"\d")

    def test_model_text_is_lowercase_and_matches_checkpoint_alphabet(self):
        alphabet = " !'(),-.:;=?abcdefghijklmnoprstuvyæñāēīōśşūǣḍḥḷṁṅṇṉṛṝṭ"
        got = worker.prepare_model_text("signal 18.25", lambda _text: "XQWZ 123", alphabet)
        self.assertEqual(got, "kskvs")
        self.assertNotRegex(got, r"[A-Z\d]")
        self.assertTrue(set(got) <= set(alphabet))


if __name__ == "__main__":
    unittest.main(verbosity=2)
