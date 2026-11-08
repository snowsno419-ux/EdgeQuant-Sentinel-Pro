"""Plan exact-identity GOLD LIMIT VIP original-message edits, without sending orders.

This module never guesses trades from GOLD/symbol-only messages. Only a Telegram
MessageEdited with the SAME chat ID + original message ID can use this route.
It does not create new positions, or re-execute an already filled order.
"""
from dataclasses import dataclass
from typing import Optional
import math
import re
from edgequant_vip_format import SIGNAL


@dataclass(frozen=True)
class SignalState:
    side: str
    entries: tuple
    sl: float
    tp: float


def read_signal(text) -> Optional[SignalState]:
    flat = re.sub(r'\s+', ' ', str(text or '').replace(' | ', ' '))
    m = SIGNAL.search(flat)
    if not m:
        return None
    side = m.group(1).upper()
    entries = sorted(set((float(m.group(2)), float(m.group(3) or m.group(2)))))
    sl, tp = float(m.group(4)), float(m.group(5))
    if len(entries) not in (1, 2) or not all(math.isfinite(v) and v > 0 for v in entries + [sl, tp]):
        return None
    if side == 'BUY':
        valid = sl < min(entries) and tp > max(entries)
    else:
        valid = sl > max(entries) and tp < min(entries)
    return SignalState(side, tuple(entries), sl, tp) if valid else None


def plan_edited_original(text, chat_id, message_id, rows, *, digits=2,
                         quick_pips=50.0, pip_size=0.10):
    """Return (per-ticket modifications, reason) by original Telegram message ID.

    Quick L1 TP stays at entry +/- 50 pips; L2 tracks the channel TP. Range
    entry levels map in sorted order only when the original/new counts match.
    A live position's entry is never modified. Broker-account identity is kept.
    """
    edited = read_signal(text)
    if not edited:
        return [], 'edited post is not a complete, directionally valid GOLD BUY/SELL + SL + TP signal'
    # Outcome notices appended to full original message are NOT new trading
    # instructions and must not resurrect or edit stopped orders.
    if re.search(r'\bSL\s*HIT\b|\bTP\s*HIT\b|\bSTOP\s*LOSS\s*HIT\b|\bCLOSED\b', str(text), re.I):
        return [], 'result notice on edited original; no MT5 change'
    eligible = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            match = (int(row.get('chat_id') or 0) == int(chat_id) and
                     int(row.get('message_id') or 0) == int(message_id) and
                     int(row.get('ticket') or 0) > 0)
        except (TypeError, ValueError):
            continue
        if (match and str(row.get('source') or '').strip().casefold() == 'gold limit vip'
                and str(row.get('source_type') or '').upper() == 'LIMIT'
                and str(row.get('status') or '').lower() in ('pending', 'open', 'partial')):
            eligible.append(row)
    if not eligible:
        return [], 'no journaled live tickets linked to edited Telegram chat/message ID'
    original = read_signal(eligible[0].get('signal'))
    if not original or edited.side != original.side:
        return [], 'original signal missing or BUY/SELL direction changed; no automatic modification'
    if len(original.entries) != len(edited.entries):
        return [], 'entry-range count changed; cannot safely map individual signal levels'
    mapping = dict(zip(original.entries, edited.entries))
    actions = []
    seen = set()
    for row in eligible:
        try:
            src = float(row.get('sig_entry') or 0)
            ticket = int(row.get('ticket') or 0)
            broker = str(row.get('broker') or '')
            tag = str(row.get('tag') or '').lower()
            state = str(row.get('status') or '').lower()
            live_sl = float(row.get('sl_now') or 0)
            live_tp = float(row.get('tp_now') or 0)
            live_price = float(row.get('open_price') or row.get('price') or 0)
        except (TypeError, ValueError):
            return [], 'journal has malformed entry/ticket/SL/TP; no automatic modification'
        if not broker or not tag or ticket <= 0 or not math.isfinite(src):
            return [], 'journal has a ticket without broker/layer/entry; no automatic modification'
        key = (broker, ticket)
        if key in seen:
            return [], 'duplicate broker+ticket in linked journal rows'
        seen.add(key)
        if src not in mapping:
            return [], 'journal contains an unmapped original range entry'
        is_quick = tag.startswith('quick')
        if not is_quick and not (tag.startswith('tp') or tag.startswith('mid')):
            return [], 'unrecognized layer tag; no automatic modification'
        desired_src = mapping[src]
        new_entry = round(desired_src + (0.99 if edited.side == 'BUY' else -0.90), digits)
        new_sl = round(edited.sl + (0.20 if edited.side == 'BUY' else -0.20), digits)
        new_tp = (round(new_entry + quick_pips * pip_size if edited.side == 'BUY'
                        else new_entry - quick_pips * pip_size, digits)
                  if is_quick else round(edited.tp, digits))
        if ((edited.side == 'BUY' and not (new_sl < new_entry < new_tp)) or
                (edited.side == 'SELL' and not (new_tp < new_entry < new_sl))):
            return [], 'edited levels conflict with fixed entry offset / 50-pip quick target'
        # A TP-only edit must NOT reset an already moved SL. When the source
        # explicitly changes its SL, never weaken an existing profit lock.
        source_sl_changed = abs(edited.sl - original.sl) > 1e-8
        protected_lock = ((edited.side == 'BUY' and live_sl >= live_price > 0 and new_sl < live_sl) or
                          (edited.side == 'SELL' and 0 < live_sl <= live_price and new_sl > live_sl))
        entry_change = abs(desired_src - src) > 1e-8
        if state != 'pending' and entry_change:
            # Already filled entry is immutable; other SL/TP edits still valid.
            entry_value = None
        else:
            entry_value = new_entry if entry_change else None
        sl_value = (new_sl if source_sl_changed and not protected_lock and
                    abs(new_sl - live_sl) > 1e-8 else None)
        tp_value = new_tp if abs(new_tp - live_tp) > 1e-8 and (not is_quick or (entry_change and state == 'pending')) else None
        if entry_value is not None or sl_value is not None or tp_value is not None:
            actions.append({'broker': broker, 'ticket': ticket, 'kind': state,
                            'entry': entry_value, 'sl': sl_value, 'tp': tp_value,
                            'original_entry': src, 'new_source_entry': desired_src,
                            'is_quick': is_quick})
    return actions, 'exact Telegram original-message edit matched'
