"""Read-only, broker-confirmed daily LIMIT order classification.

Only deals with entry IN/INOUT prove activation. Unknown broker states are
reported separately, never silently counted as untriggered.
"""
from datetime import datetime


def classify(orders, deals, limit_types, *, magic=None):
    limit_types = set(limit_types)
    entry_orders = {int(getattr(d, 'order', 0) or 0) for d in deals
                    if int(getattr(d, 'entry', -1)) in (0, 2)}
    activated, untriggered, unknown = [], [], []
    for o in orders:
        if int(getattr(o, 'type', -1)) not in limit_types:
            continue
        if magic and int(getattr(o, 'magic', 0) or 0) != int(magic):
            continue
        ticket = int(getattr(o, 'ticket', 0) or 0)
        row = {'ticket': ticket, 'symbol': str(getattr(o, 'symbol', '')),
               'volume': float(getattr(o, 'volume_initial', 0) or 0),
               'entry': float(getattr(o, 'price_open', 0) or 0),
               'placed': datetime.fromtimestamp(int(getattr(o, 'time_setup', 0) or 0)).strftime('%H:%M')}
        if ticket in entry_orders:
            activated.append(row)
        elif int(getattr(o, 'state', -1)) in (2, 3, 4):  # CANCELED, PARTIAL, FILLED; needs broker deal verification
            unknown.append(row)
        elif int(getattr(o, 'state', -1)) in (1, 5, 6, 7):  # STARTED/REJECTED/EXPIRED/REQUEST_* not all safe to infer
            unknown.append(row)
        else:
            unknown.append(row)
    # Only explicitly canceled/expired, zero-filled orders can be safely called untriggered.
    # Broker constants vary; the caller supplies confirmed terminal states below.
    return {'activated': activated, 'untriggered': untriggered, 'unknown': unknown}


def classify_with_states(orders, deals, limit_types, *, magic=None, canceled=2, expired=6):
    result = classify(orders, deals, limit_types, magic=magic)
    by_ticket = {int(getattr(o, 'ticket', 0) or 0): o for o in orders}
    keep = []
    for row in result['unknown']:
        order = by_ticket[row['ticket']]
        if int(getattr(order, 'state', -1)) in (canceled, expired) and \
                float(getattr(order, 'volume_current', 0) or 0) >= float(getattr(order, 'volume_initial', 0) or 0) - 1e-8:
            result['untriggered'].append(row)
        else:
            keep.append(row)
    result['unknown'] = keep
    return result
