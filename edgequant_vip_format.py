"""Opt-in GOLD LIMIT VIP message interpretation. No MT5 actions occur here.

Supply chat_id/message_id/reply_to_id from Telegram events, not screenshots.
An update is never attached to a trade by symbol alone.
"""
from dataclasses import dataclass, asdict
import re
from typing import Optional

NUM = r'\d{3,5}(?:\.\d+)?'
SIGNAL = re.compile(r'\bGOLD\s+(BUY|SELL)(?:\s+LIMIT)?\s+('+NUM+r')(?:\s*[-–]\s*('+NUM+r'))?(?:\s+SL\s*[:=]?\s*('+NUM+r'))?(?:\s+TP\s*[:=]?\s*('+NUM+r'))?\b', re.I | re.S)
BE_NOTE = re.compile(r'\b(?:OR\s+YOU\s+CAN\s+)?BE\s+ON\s+(\d+)\s*PIPS?\b', re.I)

@dataclass(frozen=True)
class Interpretation:
    kind: str
    action: str
    channel_id: int
    message_id: int
    reply_to_id: Optional[int]
    side: Optional[str] = None
    entry_low: Optional[float] = None
    entry_high: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    advisory_be_pips: Optional[int] = None
    confidence: str = 'unverified'
    reason: str = ''
    new_entry: Optional[float] = None
    new_tp: Optional[float] = None
    new_sl: Optional[float] = None

    def to_dict(self):
        return asdict(self)


def interpret(text, *, channel_id, message_id, reply_to_id=None, enabled_channel_ids=()):
    """Classify only for explicitly enabled channel IDs; default is disabled.

    Return None for other channels. Never infer broker order type from a header.
    """
    if int(channel_id) not in set(map(int, enabled_channel_ids)):
        return None
    raw = str(text or '').strip()
    normalized = re.sub(r'\s+', ' ', raw)
    quoted = re.search(r'GOLD LIMIT VIP\s*\n', raw, re.I)
    m = SIGNAL.search(normalized)
    if m and not quoted:
        side = m.group(1).upper()
        a = float(m.group(2)); b = float(m.group(3) or m.group(2))
        sl = float(m.group(4)) if m.group(4) else None
        tp = float(m.group(5)) if m.group(5) else None
        # Optional SL/TP are allowed; the direct-limit planner supplies
        # deterministic 50-pip SL and 150-pip TP fallbacks.
        # Do not discard an explicit BUY/SELL just because supplied protective
        # levels are on the wrong side; the broker validates actual requests.
        be = BE_NOTE.search(normalized)
        return Interpretation('signal', 'candidate', int(channel_id), int(message_id), reply_to_id,
                              side, min(a,b), max(a,b), sl, tp,
                              int(be.group(1)) if be else None, 'parsed',
                              'Direct LIMIT dispatch preserves signaled entry; missing stops/targets use owner defaults')
    # Do not let quoted signal bodies become new orders or trigger BE from the
    # parenthesized advisory note. Only commentary following the quoted signal
    # is eligible for a management instruction.
    if quoted:
        tail = raw[quoted.end():]
        tail = re.sub(r'^\s*GOLD\s+(?:BUY|SELL)[^\n]*', '', tail, flags=re.I)
        tail = re.sub(r'\bSL\s*'+NUM+r'\b|\bTP\s*'+NUM+r'\b', '', tail, flags=re.I)
        tail = BE_NOTE.sub('', tail)
        normalized = re.sub(r'\s+', ' ', tail).strip()
    lower = normalized.casefold()
    # An advisory alone must never modify the broker's stop loss.
    if not normalized or (BE_NOTE.fullmatch(normalized.strip(' ()⚠️'))):
        return Interpretation('other', 'ignore', int(channel_id), int(message_id), reply_to_id)
    # Conflicting instructions in one post must not cause an accidental close.
    if (re.search(r'\bhold\b|හෝල්ඩ්', lower) and
            re.search(r'\b(?:close|exit)\b|ක්ලෝස්|වහන්න', lower)):
        return Interpretation('update', 'unresolved', int(channel_id), int(message_id), reply_to_id,
                              reason='conflicting hold and close instructions')
    # English + Sinhala + Singlish explicit field change instructions.
    # The post must include both a named field and a change verb. Bare TP/SL
    # prices, profit recaps, and advisory 50-pip BE notes are not modifications.
    editing = re.search(
        r'\b(?:change|changed|modify|modified|update|updated|edit|edited|'
        r'wenas|maru|kranna|karanna|karanawa|danna|danawa)\b|'
        r'වෙනස්|මාරු|කරන්න|දාන්න', lower)
    target_tp = re.search(r'\bTP\s*(?:PRICE\s*)?(?:EKA\s*)?(?:TO\s*|=\s*|:\s*)?('
                          + NUM + r')(?=\b|TA\b|ට)', normalized, re.I)
    target_sl = re.search(r'\bSL\s*(?:PRICE\s*)?(?:EKA\s*)?(?:TO\s*|=\s*|:\s*)?('
                          + NUM + r')(?=\b|TA\b|ට)', normalized, re.I)
    if re.search(r'\bsl\s*hit\b|\bstop\s*loss\s*hit\b', lower):
        action = 'sl_hit_notice'
    elif editing and target_tp and not target_sl:
        action = 'tp_update_request'
    elif editing and target_sl and not target_tp:
        action = 'sl_update_request'
    elif editing and target_sl and target_tp:
        action = 'unresolved'
    elif re.search(r'\b(?:close|exit)\b|ක්ලෝස්|වහන්න', lower):
        action = 'close_request'
    elif re.search(r'\bhold\b|හෝල්ඩ්|හෝල්ඩ්\s*කරන්න', lower):
        action = 'hold_request'
    elif re.search(r'\b(?:cancel|do\s*not\s*enter|don.t\s*enter)\b|ගන්න\s*එපා', lower):
        action = 'cancel_entry_request'
    elif re.search(r'\b(?:move|set|put|කරන්න|දාන්න)\b.{0,35}\b(?:be|break\s*even)\b|\b(?:be|break\s*even)\b.{0,30}\b(?:now|කරන්න|දාන්න)\b', lower):
        action = 'be_request'
    elif re.search(r'\b(?:buy|sell)\b|\b(?:entry|enter)\b|ගන්න|මෙතනින්', lower):
        action = 'entry_update_request'
    else:
        return Interpretation('other', 'ignore', int(channel_id), int(message_id), reply_to_id)
    # Entry edits require a single explicit replacement price and an instruction.
    # A quoted original signal or price range must never supply the new price.
    new_entry = None
    if action == 'entry_update_request':
        replacement = re.search(
            r'(?i)\b(?:new\s+entry|change\s+entry\s+to|entry\s*(?:eka\s*)?(?:(?:to|at|:|=)\s*)?|'
            r'enter\s*(?:at|from)|buy\s*(?:at|from)|sell\s*(?:at|from))\s*'
            r'(\d{3,5}(?:\.\d+)?)(?=\b|ta\b|ට)', normalized)
        if not replacement and editing:
            replacement = re.search(r'(?i)\b(?:buy|sell)\s+(' + NUM + r')(?=\b|ta\b|ට)', normalized)
        if replacement and not re.search(r'\d\s*[-–]\s*\d', normalized):
            new_entry = float(replacement.group(1))
    return Interpretation('update', action, int(channel_id), int(message_id), reply_to_id,
                          confidence='unverified',
                          reason=('Requires exact Telegram reply/edit linkage and recorded broker tickets; '
                                  'ambiguous updates cannot modify MT5 orders'),
                          new_entry=new_entry,
                          new_tp=float(target_tp.group(1)) if action == 'tp_update_request' else None,
                          new_sl=float(target_sl.group(1)) if action == 'sl_update_request' else None)


def resolve_update(update, original_message_ids):
    """Only exact reply linkage; returns original message ID or None."""
    if not update or update.kind != 'update' or not update.reply_to_id:
        return None
    ids = set(map(int, original_message_ids))
    return int(update.reply_to_id) if int(update.reply_to_id) in ids else None
