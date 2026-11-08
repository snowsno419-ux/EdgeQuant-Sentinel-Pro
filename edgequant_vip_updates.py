"""GOLD LIMIT VIP: exact Telegram-message-linked management planner.

This module never connects to MT5. It only returns a safe, scoped plan for
confirmed message replies and recorded broker tickets. No symbol-only matching.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Plan:
    action: str
    original_message_id: int
    tickets_by_broker: dict
    reason: str = ''
    new_entry: float = None
    new_tp: float = None
    new_sl: float = None


def plan_update(interpretation, trades):
    if not interpretation or interpretation.kind != 'update':
        return None, 'not an update'
    if not interpretation.reply_to_id:
        return None, 'missing original Telegram reply ID; cannot safely match trade'
    if interpretation.action not in {'be_request', 'cancel_entry_request', 'close_request', 'entry_update_request', 'tp_update_request', 'sl_update_request'}:
        return None, 'informational/hold/entry-change update; no automatic MT5 mutation'
    if interpretation.action == 'entry_update_request':
        price = getattr(interpretation, 'new_entry', None)
        if price is None or not (0 < float(price) < 100000):
            return None, 'entry change requires one explicit new entry price'
    if interpretation.action in {'tp_update_request', 'sl_update_request'}:
        target = (getattr(interpretation, 'new_tp', None)
                  if interpretation.action == 'tp_update_request' else getattr(interpretation, 'new_sl', None))
        if target is None or not (0 < float(target) < 100000):
            return None, 'update requires a single explicit valid TP/SL price'
    cid, parent = int(interpretation.channel_id), int(interpretation.reply_to_id)
    candidates = []
    for row in trades:
        if not isinstance(row, dict):
            continue
        try:
            if int(row.get('chat_id') or 0) != cid or int(row.get('message_id') or 0) != parent:
                continue
            ticket = int(row.get('ticket') or 0)
        except (ValueError, TypeError):
            continue
        if ticket <= 0 or str(row.get('status') or '').lower() not in {'open', 'pending', 'partial'}:
            continue
        if str(row.get('source') or '').strip().casefold() != 'gold limit vip':
            continue
        if str(row.get('source_type') or '').upper() != 'LIMIT':
            continue
        broker = str(row.get('broker') or '').strip()
        if not broker:
            return None, 'recorded ticket has no broker identity'
        candidates.append((broker, ticket, str(row.get('status') or '').lower()))
    if not candidates:
        return None, 'no live journal tickets linked to original message ID'
    by_broker = {}
    for broker, ticket, status in candidates:
        if interpretation.action == 'be_request' and status == 'pending':
            continue
        if interpretation.action in {'cancel_entry_request', 'entry_update_request'} and status != 'pending':
            continue
        if interpretation.action == 'close_request' and status == 'pending':
            continue
        by_broker.setdefault(broker, [])
        if ticket not in by_broker[broker]:
            by_broker[broker].append(ticket)
    if not by_broker:
        return None, 'no eligible tickets for requested action'
    return Plan(interpretation.action, parent, by_broker,
                new_entry=getattr(interpretation, 'new_entry', None),
                new_tp=getattr(interpretation, 'new_tp', None),
                new_sl=getattr(interpretation, 'new_sl', None)), ''
