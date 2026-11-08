"""Telegram signal edit/reply planner (pure Python; no MT5 connections).

Only mutates previously journaled, active tickets with a trustworthy identity:
(1) original edit uses exact chat/message ID;
(2) reply uses the exact original chat/reply ID;
(3) an unthreaded message must quote an exact OLD source entry and uniquely
    identify a single original signal within the same chat/source/category.
Never guesses from the newest GOLD trade, or from a BUY/SELL message alone.

Multilingual field words: English, common Singlish, and Sinhala.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import re

NUM = r'(\d{1,6}(?:[.,]\d{1,5})?)'
# Sinhala and transliterated words that can introduce numeric fields.
FILL = r'(?:\s|:|=|@|\-|එක|එකේ|එකට|එකත්|මිල|eka|eke|ekata|ekath|price|ta|ට|ටම|වෙත|to|at|is|walata|danna|දාන්න){0,18}'
ENTRY = r'(?:\bentry\s*eka\b|\bentry\b|\bentr[yie]\b|\benter\b|\bprice\b|\bentri\b|\bentryprice\b|එන්ට්‍රි(?:ය|යක්)?|ඇන්ට්‍රි(?:ය)?|ඇතුල්වීම(?:ේ)?|ප්‍රවේශ\s*මිල)'
STOP = r'(?:\bSL\b|\bstop\s*loss\b|\bstoploss\b|ස්ටොප්\s*ලොස්|ස්ටොප්ලොස්|පාඩු\s*සීමාව|පාඩු\s*නවත්වන\s*මිල)'
TARGET = r'(?:\bTP\s*2?\b|\btake\s*profit\b|\btarget\b|ටේක්\s*ප්‍රොෆිට්|ටාගට්|ලාභ\s*ඉලක්කය)'
# No number-only guessing for SL / TP; a label must be present.
ENTRY_RE = re.compile(r'(?i)(?:' + ENTRY + r')' + FILL + NUM)
SL_RE = re.compile(r'(?i)(?:' + STOP + r')' + FILL + NUM)
TP_RE = re.compile(r'(?i)(?:' + TARGET + r')' + FILL + NUM)
SIDE_RE = re.compile(r'(?i)\b(BUY|SELL|LONG|SHORT)\b|\b(බයි|සෙල්)\b')
SYMBOL_RE = re.compile(r'(?i)\b(XAUUSD[a-z0-9._]*|GOLD|EURUSD[a-z0-9._]*|AUDUSD[a-z0-9._]*|USDCAD[a-z0-9._]*|NZDUSD[a-z0-9._]*|GBPUSD[a-z0-9._]*|USDJPY[a-z0-9._]*)\b')
COMPLETE_RE = re.compile(r'(?i)\b(?:GOLD|XAUUSD[a-z0-9._]*)\s+(BUY|SELL)\s*' + NUM + r'(?:\s*[-–]\s*' + NUM + r')?')
UPDATE_WORDS_RE = re.compile(r'(?i)\b(?:change|changed|move|moving|modify|modified|update|updated|adjust|adjusted|instead|from|to|new|now|entry|enter|price|ganna|gana|ganne|danna|tiyanna|thiyanna|wenas|wena\s*karanna|wens\s*karanna|hari|meka|meeke|me\s*signal)\b|වෙනස්|වෙනස්\s*කරන්න|දාන්න|ගන්න|ගන්නේ|තියන්න|තිබ්බ|තබන්න|ඇතුල්වීම|එන්ට්‍රි|මේක|මේකේ')
RESULT_ONLY_RE = re.compile(r'(?i)\b(?:SL\s*HIT|TP\s*HIT|STOP\s*LOSS\s*HIT|CLOSED|RESULT|PROFIT\s*BOOKED)\b|ස්ටොප්\s*ලොස්\s*වැදුණ|ප්‍රොෆිට්\s*වුනා')
ADVISORY_RE = re.compile(r'(?i)\b(?:maybe|might|could|if|optional|risk\s*takers?|or\s+you\s+can|BE\s+on|BE\s+after|when\s+in\s+profit)\b|කැමති\s*නම්|පුළුවන්\s*නම්|ඕන(?:ේ)?\s*නම්')
# Require actual instruction for unlabelled numeric entry; scoped to an exact reply.
UNLABELLED_ENTRY_RE = re.compile(r'(?i)\b(?:ganna|ganne|danna|take|enter|enter\s+at|buy\s+at|sell\s+at)\b|ගන්න|ගන්නේ|දාන්න|මිලට\s*ගන්න')
OLD_ENTRY_RE = re.compile(r'(?i)\b(?:old\s*entry|previous\s*entry|original\s*entry|from\s*entry|mulin\s*entry|kalin\s*entry)\s*(?:was\s*)?[:=@]?\s*' + NUM)
OLD_ENTRY_FROM = re.compile(r'(?i)\bfrom\s*' + NUM + r'\s*(?:to|->|→)\s*' + NUM)
OLD_ENTRY_ALT = re.compile(r'(?i)\b(?:entry\s*(?:was|had\s*been|at)\s*|mulin\s*|kalin\s*)' + NUM + r'\s*(?:to|->|→|now|dan|wenuwata)\b')
FULL_GOLD = re.compile(r'(?i)\b(?:GOLD|XAUUSD[a-z0-9._]*)\s+(?:BUY|SELL)\b')


def price(token):
    try:
        val = float(str(token).replace(',', '.'))
        return val if math.isfinite(val) and val > 0 else None
    except (TypeError, ValueError):
        return None


def side_of(text):
    m = SIDE_RE.search(text)
    if not m:
        return None
    val = m.group(1).upper() if m.group(1) else m.group(2)
    return 'BUY' if val in ('BUY', 'LONG', 'බයි') else 'SELL'


def symbol_of(text):
    m = SYMBOL_RE.search(text)
    if not m:
        return None
    s = m.group().upper()
    return 'XAUUSD' if s == 'GOLD' or s.startswith('XAUUSD') else s


def sym_matches(a, b):
    a = str(a or '').upper().replace('GOLD', 'XAUUSD')
    b = str(b or '').upper().replace('GOLD', 'XAUUSD')
    if not a or not b:
        return False
    a = re.split(r'[.#]', a, maxsplit=1)[0]
    b = re.split(r'[.#]', b, maxsplit=1)[0]
    return a == b or (a.startswith(b) and len(a) - len(b) <= 4) or (b.startswith(a) and len(b) - len(a) <= 4)


@dataclass(frozen=True)
class Change:
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    side: str | None = None
    symbol: str | None = None
    full_entries: tuple = ()
    old_entry: float | None = None
    short_entry: bool = False
    complete: bool = False


def parse_change(text, *, original_edit=False, is_reply=False):
    raw = str(text or '').replace('−', '-').replace('–', '-').replace('—', '-')
    flat = re.sub(r'\s+', ' ', raw).strip()
    if not flat or RESULT_ONLY_RE.search(flat):
        return None, 'outcome/advisory notice, not an edit instruction'
    full = COMPLETE_RE.search(flat)
    explicit_intent = bool(UPDATE_WORDS_RE.search(flat))
    # An exact Telegram reply carrying a revised complete signal can be an
    # update, even when no 'change' verb is used. The journal match later
    # requires that exact reply-to message ID, source, side and symbol.
    if not original_edit and not explicit_intent and not is_reply:
        return None, 'no explicit management instruction'
    if not original_edit and not (full and is_reply) and ADVISORY_RE.search(flat) and not re.search(r'(?i)\b(?:change|move|modify|update|instead|danna|ganna|tiyanna)\b|වෙනස්\s*කරන්න|දාන්න|ගන්න|තියන්න', flat):
        return None, 'conditional/advisory text is not a mandatory update'
    sl_m = list(SL_RE.finditer(flat))[-1] if SL_RE.search(flat) else None
    tp_m = list(TP_RE.finditer(flat))[-1] if TP_RE.search(flat) else None
    entry_m = list(ENTRY_RE.finditer(flat))[-1] if ENTRY_RE.search(flat) else None
    sl = price(sl_m.group(1)) if sl_m else None
    tp = price(tp_m.group(1)) if tp_m else None
    entry = price(entry_m.group(1)) if entry_m else None
    old_m = OLD_ENTRY_RE.search(flat) or OLD_ENTRY_ALT.search(flat) or OLD_ENTRY_FROM.search(flat)
    old_entry = price(old_m.group(1)) if old_m else None
    if old_m and old_m.re is OLD_ENTRY_FROM:
        entry = price(old_m.group(2))
    full_entries = ()
    short_entry = False
    side = side_of(flat)
    symbol = symbol_of(flat)
    if full:
        side = full.group(1).upper()
        if not is_reply and not original_edit and entry is not None and old_entry is None:
            # A separate follow-up can quote the ORIGINAL full GOLD price and
            # give a distinctly labelled replacement entry; use that exact
            # old price as the channel-scoped reference, not 'latest GOLD'.
            old_entry = price(full.group(2))
        v1, v2 = price(full.group(2)), price(full.group(3)) if full.group(3) else None
        full_entries = tuple(sorted(set(v for v in (v1, v2) if v)))
        if original_edit:
            entry = None  # map full original entries to old groups, not field scan
            # A channel operator may edit the original post and append
            # "මේක ගන්න 24.25 ගනේ" after the full GOLD ... SL ... TP line.
            # Treat ONLY one explicit trailing instruction price as a new
            # source entry, resolved relative to the one original entry.
            if len(full_entries) == 1:
                tail = flat[full.end():]
                if tp_m is not None:
                    tail = flat[max(full.end(), tp_m.end()):]
                tail = re.sub(r'(?i)\bBE\s*(?:on|at|after)?\s*\d+(?:[.,]\d+)?\s*(?:pips?)?', '', tail)
                if UNLABELLED_ENTRY_RE.search(tail) and not (ENTRY_RE.search(tail) or SL_RE.search(tail) or TP_RE.search(tail)):
                    trailing = [price(m.group()) for m in re.finditer(r'(?<![\w.])\d{1,6}(?:[.,]\d{1,5})?(?![\w.])', tail)]
                    trailing = [v for v in trailing if v is not None]
                    if len(trailing) == 1:
                        entry = trailing[0]
                        short_entry = True
                        full_entries = ()
        if is_reply and not original_edit and not entry and len(full_entries) == 1:
            entry = full_entries[0]
    if entry is None and not full and is_reply and UNLABELLED_ENTRY_RE.search(flat):
        # Allow short XAU prices such as "meka ganna 24.25 gane" ONLY when
        # exactly one numeric price exists in the reply; resolved later using
        # the journaled original price and exact reply reference.
        nums = re.findall(r'(?<![\w.])\d{1,6}(?:[.,]\d{1,5})?(?![\w.])', flat)
        vals = [price(x) for x in nums]
        vals = [v for v in vals if v]
        if len(vals) == 1 and sl is None and tp is None:
            entry, short_entry = vals[0], True
    if original_edit and not full_entries and entry is None and sl is None and tp is None:
        return None, 'edited message has no interpretable prices'
    if not original_edit and entry is None and sl is None and tp is None:
        return None, 'no explicit entry, SL, or TP change'
    if not original_edit and not is_reply and old_entry is None:
        return None, 'unthreaded change must specify the exact OLD entry'
    return Change(entry, sl, tp, side, symbol, full_entries, old_entry, short_entry,
                  bool(full and sl and tp)), 'parsed explicit signal update'


def resolve_shorthand(value, original_entry, symbol):
    """Only expand e.g. 24.25 -> 3924.25 when original was 3925.

    Reject 24.25 without one exact linked original, far prices and other markets.
    """
    if not str(symbol).upper().startswith('XAU') or value >= 1000 or original_entry < 1000:
        return value
    base = math.floor(original_entry / 100) * 100
    candidates = [base - 100 + value, base + value, base + 100 + value]
    nearest = min(candidates, key=lambda p: abs(p - original_entry))
    return nearest if abs(nearest - original_entry) <= 20 else None


def plan_changes(change, rows, *, mode, source, chat_id, category,
                 original_message_id=None, quick_pips=50, pip_size=0.1, digits=2):
    """Return validated ticket-specific edits; never applies to MT5 itself."""
    if change is None:
        return [], 'no recognized update'
    active = {'pending', 'open', 'partial'}
    source_key = str(source or '').casefold().strip()
    cat_key = str(category or '').upper().strip()
    cid = int(chat_id or 0)
    matches = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        try:
            if int(r.get('chat_id') or 0) != cid or int(r.get('message_id') or 0) <= 0:
                continue
            if original_message_id and int(r.get('message_id') or 0) != int(original_message_id):
                continue
            if int(r.get('ticket') or 0) <= 0 or str(r.get('status') or '').lower() not in active:
                continue
            # Telegram chat ID is the stable source identity even when a
            # provider renames the channel/group. Never infer a chat from
            # its title alone.
            if str(r.get('source_type') or '').upper() != cat_key:
                continue
            if change.side and change.side != str(r.get('direction') or '').upper():
                continue
            if change.symbol and not sym_matches(change.symbol, r.get('symbol')):
                continue
            if change.old_entry is not None and abs(float(r.get('sig_entry') or 0) - change.old_entry) > 1e-6:
                continue
        except (TypeError, ValueError):
            continue
        matches.append(r)
    if not matches:
        return [], 'no active, exactly scoped MT5 tickets found'
    ids = {int(r['message_id']) for r in matches}
    if len(ids) != 1:
        return [], 'unthreaded reference matches multiple original signals; no guessing'
    brokers = set()
    for r in matches:
        broker = str(r.get('broker') or '').strip()
        if not broker:
            return [], 'one journal record has no MT5 broker identity'
        key = (broker.casefold(), int(r['ticket']))
        if key in brokers:
            return [], 'duplicate broker/ticket in journal'
        brokers.add(key)
    source_entries = sorted({float(r.get('sig_entry') or 0) for r in matches})
    if not source_entries or min(source_entries) <= 0:
        return [], 'missing original source entry in journal'
    mapping = {}
    if change.full_entries and (mode == 'original_edit' or (mode == 'followup' and change.entry is None)):
        if len(change.full_entries) != len(source_entries):
            return [], 'edited original entry count differs from journal entries'
        mapping = dict(zip(source_entries, change.full_entries))
    elif change.entry is not None:
        if len(source_entries) != 1:
            return [], 'multiple entry levels: specify exact OLD entry and reply to its signal'
        new_src = float(change.entry)
        if change.short_entry:
            new_src = resolve_shorthand(new_src, source_entries[0], matches[0].get('symbol'))
            if new_src is None:
                return [], 'shorthand entry cannot be resolved near the original Gold entry'
        mapping[source_entries[0]] = new_src
    actions = []
    for r in matches:
        old_src = float(r['sig_entry'])
        old_price = float(r.get('price') or r.get('open_price') or 0)
        side = str(r.get('direction') or '').upper()
        symbol = str(r.get('symbol') or '')
        status = str(r.get('status') or '').lower()
        tag = str(r.get('tag') or '').lower()
        old_sl = float(r.get('sl_now') or 0)
        old_tp = float(r.get('tp_now') or 0)
        dest_src = mapping.get(old_src, old_src)
        if not math.isfinite(dest_src) or dest_src <= 0 or old_price <= 0 or side not in ('BUY', 'SELL'):
            return [], 'invalid stored direction or entry'
        # Preserve the exact original broker-specific entry offset, if any:
        # e.g. original XAU BUY 4000 was placed at 4000.99 -> edited 4050.99.
        offset = old_price - old_src
        # Do not infer a huge spread adjustment from a stale/filled journal.
        if abs(offset) > (2 if symbol.upper().startswith('XAU') else max(5 * float(r.get('pip') or pip_size), 0.01)):
            offset = 0.0
        pending = status == 'pending'
        entry_changed = abs(dest_src - old_src) > 1e-8
        effective_digits = int(digits)
        row_pip = float(r.get('pip') or pip_size)
        if row_pip <= 0.0001:
            effective_digits = max(effective_digits, 5)
        elif 'JPY' in symbol.upper():
            effective_digits = max(effective_digits, 3)
        elif abs(old_price * 1000 - round(old_price * 1000)) < 1e-6 and abs(old_price * 100 - round(old_price * 100)) > 1e-6:
            effective_digits = max(effective_digits, 3)
        live_entry = round(dest_src + offset, effective_digits)
        new_entry = live_entry if pending and entry_changed else None
        is_quick = tag.startswith('quick') or str(r.get('layer') or '').startswith('1')
        new_sl = float(change.sl) if change.sl is not None else None
        new_tp = None
        if is_quick:
            if entry_changed and pending:
                new_tp = round(live_entry + (1 if side == 'BUY' else -1) * float(quick_pips) * float(r.get('pip') or pip_size), effective_digits)
        elif change.tp is not None:
            new_tp = round(float(change.tp), effective_digits)
        if new_sl is not None:
            new_sl = round(new_sl, effective_digits)
        # Don't reverse an existing BE/profit lock on a filled position.
        filled_price = float(r.get('open_price') or old_price)
        profit_locked = (status != 'pending' and old_sl > 0 and filled_price > 0 and
                         (old_sl >= filled_price if side == 'BUY' else old_sl <= filled_price))
        if profit_locked and new_sl is not None and ((side == 'BUY' and new_sl < old_sl) or
                                                     (side == 'SELL' and new_sl > old_sl)):
            new_sl = None
        if new_sl is not None and abs(new_sl - old_sl) < 1e-8:
            new_sl = None
        if new_tp is not None and abs(new_tp - old_tp) < 1e-8:
            new_tp = None
        # A filled position cannot accept an entry adjustment. Other valid
        # SL/TP modifications may still be submitted by exact ticket.
        if new_entry is None and new_sl is None and new_tp is None:
            continue
        actions.append(dict(broker=str(r.get('broker')), ticket=int(r['ticket']),
                            kind='PENDING' if pending else 'OPEN', entry=new_entry,
                            sl=new_sl, tp=new_tp, symbol=symbol, direction=side,
                            source_entry=dest_src, old_source_entry=old_src,
                            is_quick=is_quick, message_id=int(r['message_id'])))
    if not actions:
        return [], 'no change to active MT5 tickets (or entry already filled)'
    return actions, f'{len(actions)} exact-ticket modification(s) planned for source message #{next(iter(ids))}'
