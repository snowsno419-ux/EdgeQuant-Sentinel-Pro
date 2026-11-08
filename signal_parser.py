"""
Telegram signal -> MT5 pending order parser.

Pure standard library (no network / no MT5 needed), so it can be unit tested
anywhere:  python3 test_parser.py

Supported signal styles (examples):
    XAUUSD BUY LIMIT 2650
    SL 2640
    TP 2660 / TP2 2670

    🟢 EURUSD BUY LIMIT @ 1.0850
    SL: 1.0800   TP: 1.0900

    Sell Limit GOLD 2675-2678   SL 2685   TP 2665
    USDCAD SELL LIMIT  Entry: 1.3620  SL: 50 pips  TP: 100 pips
    XAUUSD SELL LIMIT 2.678,50  SL 2.690,00  TP 2.650,00
    CANCEL ALL PENDING EURUSD
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Optional, Sequence

# --------------------------------------------------------------------------- #
# number building blocks
# --------------------------------------------------------------------------- #
NUM = r"(?:\d{1,3}(?:[ \u00a0,.]\d{3})+(?:[.,]\d+)?(?!\d)|\d+(?:[.,]\d+)?)"
PIP = r"\d+(?:[.,]\d+)?\s*(?:PIPS?|POINTS?|PTS?)\b"
VALUES = NUM + r"(?:\s*(?:-|/|&|\+|,|\bTO\b|\bAND\b)\s*" + NUM + r")*"

FALLBACK_SYMBOLS = [
    "XAUUSD", "XAGUSD", "XPTUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY",
    "EURAUD", "EURCHF", "CADJPY", "CHFJPY", "NZDJPY", "GBPCHF", "GBPAUD",
    "GBPCAD", "GBPNZD", "AUDCAD", "AUDCHF", "AUDNZD", "EURNZD", "EURCAD",
    "CADCHF", "NZDCAD", "NZDCHF", "USDTRY", "USDZAR", "USDMXN", "US30",
    "US100", "US500", "GER40", "UK100", "JP225", "USOIL", "UKOIL",
    "BTCUSD", "ETHUSD",
]

DEFAULT_ALIASES = {
    "GOLD": "XAUUSD", "XAU": "XAUUSD", "SILVER": "XAGUSD", "XAG": "XAGUSD",
    "PLATINUM": "XPTUSD", "WTI": "USOIL", "CRUDE": "USOIL", "OIL": "USOIL",
    "BRENT": "UKOIL", "DOW": "US30", "DOWJONES": "US30", "DJ30": "US30",
    "SPX": "US500", "SP500": "US500", "SPX500": "US500", "NAS100": "US100",
    "NASDAQ": "US100", "USTEC": "US100", "DAX": "GER40", "DAX40": "GER40",
    "FTSE": "UK100", "NIKKEI": "JP225", "BITCOIN": "BTCUSD", "ETHEREUM": "ETHUSD",
}

# per-symbol pip size used only when the signal gives SL/TP in PIPs
DEFAULT_PIP_SIZES = {
    "XAUUSD": 0.1, "XAGUSD": 0.01, "US30": 1.0, "US100": 1.0, "US500": 0.1,
    "GER40": 1.0, "UK100": 1.0, "JP225": 1.0, "USOIL": 0.01, "UKOIL": 0.01,
}
DEFAULT_PIP_FX = 0.0001  # 4-digit FX pairs
JPY_PIP = 0.01

# --------------------------------------------------------------------------- #
# regexes
# --------------------------------------------------------------------------- #
DIRECTION_RE = re.compile(r"\b(BUY|SELL|LONG|SHORT)\b")
ORDERTYPE_RE = re.compile(r"\b(LIMIT|STOP|MARKET|INSTANT|NOW)\b")

# SL / STOP LOSS ... also the typos channels make: "STOP LOST", "STOPLOSE", "STL"
SL_RE = re.compile(
    r"\b(?:S[./]?L|STL|STOP[\s_.-]?LOS[ST]|STOP[\s_.-]?LOSE|STOPLOS[ST])\b"
    r"\s*(?:IS|AT)?\s*[:=\-@]?\s*(?:(?P<pips>" + PIP + r")|(?P<val>" + VALUES + r"))", re.I)
TP_RE = re.compile(
    r"\b(?:TP|T/?P|TARGETS?|TAKE[\s_-]?PROFIT|PROFIT)\s*([1-9])?\b\s*(?:IS|AT)?\s*[:=\-@]?\s*(?:(?P<pips>"
    + PIP + r")|(?P<val>" + VALUES + r"))", re.I)
LOT_RE = re.compile(r"\b(?:LOTS?|VOLUME|VOL|SIZE|QTY)\b\s*[:=\-]?\s*(\d+(?:[.,]\d+)?)", re.I)
LOT_INLINE_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:LOTS?|LOT)\b", re.I)

PIP_MARK_RE = re.compile(PIP, re.I)
# Some signal channels write a two-price zone as "SELL 4173 4177" (no dash).
SPACE_RANGE_AFTER_DIRECTION_RE = re.compile(
    r"\b(?:BUY|SELL|LONG|SHORT)\b[^\d\n]{0,24}(" + NUM + r")[ \t]+(" + NUM + r")(?![\d.,])",
    re.I)

ENTRY_PATTERNS = [
    # "ENTER IN = 4185- 4178"  /  "ENTER AT 4186"  /  "ENTER NOW" (no numbers -> market)
    re.compile(r"\bENTER(?:\s+IN|\s+AT)?\b\s*[:=\-]?\s*(" + VALUES + r")", re.I),
    re.compile(r"\b(?:ENTR(?:Y|IES|EY)|EP|OPEN\s*PRICE|OPEN|PRICE)\b\s*[:=\-@]?\s*(" + VALUES + r")", re.I),
    re.compile(r"@\s*(" + VALUES + r")"),
    re.compile(r"\b(?:BUY|SELL|LONG|SHORT)\s+(?:LIMIT|STOP)\b[^0-9\n]{0,24}(" + VALUES + r")", re.I),
    re.compile(r"\b(?:LIMIT|STOP)\s+(?:BUY|SELL|LONG|SHORT)\b[^0-9\n]{0,24}(" + VALUES + r")", re.I),
    re.compile(r"\b(?:BUY|SELL|LONG|SHORT)\b[^0-9\n]{0,24}(" + VALUES + r")", re.I),
    re.compile(r"\b(?:LIMIT|STOP)\b[^0-9\n]{0,24}(" + VALUES + r")", re.I),
]

# things to strip out before looking for the entry price
NOISE_RES = [
    # 15:30 / 15:30:20 - always a time; a bare "31.80" must NOT be treated as one
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:GMT|UTC|AM|PM)?\b", re.I),
    # 15.30 GMT / 4 PM - dotted form only with an explicit timezone marker
    re.compile(r"\b\d{1,2}[.]\d{2}\s*(?:GMT|UTC|AM|PM)\b", re.I),
    re.compile(r"\b(?:R{1,2}|RISK[\s_-]?REWARD)\b\s*[:=]?\s*\d+(?::\d+(?:\.\d+)?)?", re.I),  # RR 1:3
    re.compile(r"\b\d+\s*%"),                                              # risk 1%
    re.compile(r"\(\s*\d+(?:[.,]\d+)?\s*(?:PIPS?|POINTS?|PTS?)\s*\)"),         # SL = 4117 (80 pips)
    re.compile(r"\b#\w+"),                                                 # hashtags
    # channel advice lines, e.g. "( or You can BE on 70 Pips And The n Break out
    # happened hold Above 4389 )"  -> never a trade price
    re.compile(r"\(?\s*or\s+you\s+can\s+BE\b[^\n]*", re.I),
    re.compile(r"\bbreak[\s-]?out\s+happened[^\n]*", re.I),
    re.compile(r"\bBE\b[^\n]*\bPIPS?\b", re.I),
]

CANCEL_RE = re.compile(r"\b(CANCEL|DELETE|REMOVE|KILL)\b", re.I)
PENDING_RE = re.compile(r"\b(PENDING|PENDINGS|ORDER|ORDERS|LIMIT|ENTRY|ENTRIES)\b", re.I)
CLOSE_RE = re.compile(r"\b(CLOSE|EXIT)\b", re.I)
CLOSE_ALL_RE = re.compile(r"\b(ALL|EVERYTHING)\b", re.I)
MODIFY_RE = re.compile(r"\b(MODIFY|MOVE\s*SL|BREAKEVEN|TRAIL|SECURE|TAKE\s*PROFIT)\b", re.I)
# A recap such as "4179 Hit 80 Pips Done" is an outcome/status update, not a new entry.
OUTCOME_WORD_RE = re.compile(r"\b(?:HIT|DONE|REACHED|BOOKED|CLOSED|SECURED|LOCKED|ACHIEVED)\b", re.I)
OUTCOME_METRIC_RE = re.compile(
    r"\b(?:PIPS?|TP\s*[1-9]?|S/?L|STOP[\s_-]?LOSS|TARGETS?|PROFIT|P/?L|BE)\b", re.I)

# follow-up / management messages
PARTIAL_RE = re.compile(
    r"\b(?:CLOSE|BOOK|SECURE|TAKE)\b[^\n]{0,24}?(HALF\b|1/2|\d/\d|\d{1,3}\s*%|PARTIAL\w*)", re.I)
BE_RE = re.compile(
    r"\b(?:MOVE\s+(?:MY\s+)?SL\s+TO\s+BE|SET\s+(?:THE\s+)?(?:SL\s+)?(?:TO\s+)?BE|SL\s+TO\s+BE|"
    r"SL\s+TO\s+BREAK[\s-]?EVEN|BREAK[\s-]?EVEN|BE\s+NOW|MOVE\s+TO\s+BE)\b", re.I)
BE_PIPS_RE = re.compile(r"\bBE\b[^\n\d]{0,14}(\d{1,3})\s*(?:PIPS?|POINTS?|PTS?)\b", re.I)
# "After Hit TP1, Move SL to Entry" -> move SL to the entry price (= break-even)
BE_ENTRY_RE = re.compile(r"\b(?:MOVE\s+)?SL\s*(?:TO|->|\u2192|@)\s*(?:THE\s+)?ENTR(?:Y|Y\s*PRICE)\b", re.I)
BE_AFTER_TP1_RE = re.compile(r"\bAFTER\s+(?:HIT(?:TING)?\s+)?(?:TP\s*1\b|TARGET\s*1\b|TP1\b)", re.I)
ENTRY_MISSED_RE = re.compile(
    r"\b(?:ENTR(?:Y|IES))\s+(?:MISSED|MISS|GONE|SKIPPED|OVER)\b|"
    r"\bMISS(?:ED)?\s+(?:THE\s+)?ENTR(?:Y|IES)\b", re.I)
TRAIL_RE = re.compile(r"\bTRAIL(?:ING)?\b", re.I)

# "Change All Sell Trades To TP 4135" / "Move all buy trades TP to 4200"
MODIFY_VERB_RE = re.compile(r"\b(?:CHANGE|SET|MOVE|UPDATE|SHIFT|ADJUST|MODIFY|MAKE)\b", re.I)
TARGET_RE = re.compile(r"\b(?:TP|T/?P\b|TARGETS?|TAKE[\s-]?PROFIT)\b", re.I)
CHANGE_TO_BE_RE = re.compile(r"\b(?:TO|INTO|AT)\s+(?:THE\s+)?(?:BE|BREAK[\s-]?EVEN)\b", re.I)
PENDING_SCOPE_RE = re.compile(r"\b(?:ORDERS?|PENDINGS?)\b", re.I)
STRUCTURED_ORDER_RE = re.compile(r"\b(?:BUY|SELL|LONG|SHORT)\s+(?:LIMIT|STOP)\b", re.I)

EMOJI_BUY = ("🟢", "✅", "🟩", "📈", "⬆")
EMOJI_SELL = ("🔴", "❌", "🟥", "📉", "⬇")


# --------------------------------------------------------------------------- #
# data model
# --------------------------------------------------------------------------- #
@dataclass
class Signal:
    action: str = "ignore"          # place | cancel_pending | close_all | close_symbol | unsupported | ignore
    direction: Optional[str] = None  # BUY | SELL
    order_type: Optional[str] = None  # LIMIT | STOP | MARKET
    symbol: Optional[str] = None
    entries: List[float] = field(default_factory=list)
    sl: Optional[float] = None
    tps: List[float] = field(default_factory=list)
    volume: Optional[float] = None
    fraction: Optional[float] = None  # partial close portion (0.5 = half)
    be_pips: Optional[float] = None   # "BE on 70 Pips" -> 70
    tp: Optional[float] = None        # new TP target for modify_tp
    scope: Optional[str] = None       # "positions" | "pending" for management actions
    be_after_tp1: bool = False        # "After Hit TP1, Move SL to Entry"
    entry_marked: bool = False        # entry came from an explicit "ENTER IN / ENTRY:" marker
    confidence: str = "low"          # high | medium | low
    issues: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
REACTION_EMOJI = ("[\u2764\u2665\U0001F525\U0001F44D\U0001F64F\U0001F389\U0001F60D"
                  "\U0001F970\U0001F44C\U0001F4AF\U0001F44F\U0001F602\U0001F923"
                  "\U0001F62E\U0001F631\U0001F440\u2b50]")
REACTION_COUNT_RE = re.compile(REACTION_EMOJI + r"\s*\d{1,5}\b")


def _clean(text: str) -> str:
    t = text.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2212", "-").replace("`", " ").replace("*", " ")
    # telegram reaction counts ("❤️4 🔥2") must never look like a price
    t = REACTION_COUNT_RE.sub(" ", t)
    return t


def price_candidates(token: str) -> List[float]:
    """All plausible numeric readings of a raw price token (comma/dot chaos)."""
    t = re.sub(r"[^0-9.,]", "", token or "")
    t = t.strip(".,")
    out: List[float] = []
    if not t:
        return out

    def add(x: Optional[float]) -> None:
        if x is not None and x > 0 and x not in out:
            out.append(x)

    def to_f(s: str) -> Optional[float]:
        try:
            return float(s)
        except ValueError:
            return None

    add(to_f(t.replace(" ", "")))                                 # 1085 -> 1085
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", t):
        add(to_f(t.replace(",", "")))                             # 2,650 -> 2650 ; 2.650 -> 2650
    if "," in t and "." in t:
        add(to_f(t.replace(".", "").replace(",", ".")))           # 2.678,50 -> 2678.5
        add(to_f(t.replace(",", "")))                             # 1,085.50 -> 1085.5
    m = re.fullmatch(r"(\d+)[.,](\d+)", t)
    if m:
        add(to_f(m.group(1) + "." + m.group(2)))                  # 1.0850 -> 1.085 ; 1,085 -> 1.085
    return out


def choose_price(token: str, hint: Optional[float] = None) -> Optional[float]:
    """Pick the most plausible reading. With a live price hint this is reliable:
    '1,285' for GBPUSD (hint 1.2860) -> 1.285, not 1285."""
    cands = price_candidates(token)
    if not cands:
        return None
    if hint:
        return min(cands, key=lambda x: abs(x - hint))
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", re.sub(r"[^0-9.,]", "", token)):
        return cands[0]              # "2,650" -> 2650 (thousands)
    return cands[-1]                 # otherwise trust the last separator as decimal


HIGH_PRICE_SYMBOLS = {
    "XAUUSD", "XAGUSD", "XPTUSD", "US30", "US100", "US500", "GER40", "UK100",
    "JP225", "USOIL", "UKOIL", "BTCUSD", "ETHUSD", "NAS100", "SPX500",
}


def plausible_price(symbol: Optional[str], value: float, hint: Optional[float] = None) -> bool:
    """Reject reaction counts / lot sizes / years that look like prices."""
    if value <= 0:
        return False
    if hint:
        ratio = value / hint
        return 0.2 <= ratio <= 5.0
    sym = (symbol or "").upper()
    if sym in HIGH_PRICE_SYMBOLS:
        return 10.0 <= value <= 500000.0     # gold ~4000, silver ~30, indices thousands, oil ~70
    if sym.endswith("JPY"):
        return 20.0 <= value <= 1000.0       # 150.25
    if sym:
        return 0.2 <= value <= 60.0          # FX majors + exotics (USDTRY ~35)
    return 0.0005 <= value <= 500000.0


def _split_values(blob: str) -> List[str]:
    if not blob:
        return []
    parts = re.split(r"\s*(?:-|/|&|\+|\bTO\b|\bAND\b)\s*", blob)
    return [p.strip() for p in parts if p.strip()]


def pip_size_for(symbol: str, overrides: Optional[Dict[str, float]] = None) -> float:
    if overrides and symbol in overrides:
        return float(overrides[symbol])
    if symbol in DEFAULT_PIP_SIZES:
        return DEFAULT_PIP_SIZES[symbol]
    if symbol.endswith("JPY"):
        return JPY_PIP
    return DEFAULT_PIP_FX


def _fraction(txt: str) -> float:
    """HALF / 1/2 / 50% / PARTIAL -> 0.5"""
    s = (txt or "").strip().lower()
    if s in ("half", "1/2", "partial", "partials", "partial profit", "part", "portion"):
        return 0.5
    m = re.search(r"(\d{1,3})\s*%", s)
    if m:
        return min(1.0, max(0.05, int(m.group(1)) / 100.0))
    m = re.fullmatch(r"\s*(\d)\s*/\s*(\d)\s*", s)
    if m:
        return min(1.0, int(m.group(1)) / max(1, int(m.group(2))))
    return 0.5


def find_symbol(text: str, universe: Sequence[str], aliases: Dict[str, str]) -> Optional[str]:
    t = text.upper().replace("/", "").replace("\\", "")
    names = sorted(set(list(universe) + list(aliases.keys())), key=len, reverse=True)
    for name in names:
        if re.search(r"(?<![A-Z0-9])" + re.escape(name.upper()) + r"(?![A-Z0-9])", t):
            return aliases.get(name.upper(), name.upper())
    return None


# --------------------------------------------------------------------------- #
# main entry point
# --------------------------------------------------------------------------- #
def parse_signal(
    text: str,
    symbols: Optional[Sequence[str]] = None,
    aliases: Optional[Dict[str, str]] = None,
    hint_prices: Optional[Dict[str, float]] = None,
    default_order_type: str = "LIMIT",
    pip_sizes: Optional[Dict[str, float]] = None,
    positional_fallback: bool = True,
    default_symbol: Optional[str] = None,
    fix_direction: bool = True,
) -> Signal:
    """
    text             : raw message
    symbols          : broker symbol list (or None -> built-in fallback list)
    hint_prices      : {symbol: live price} used to resolve comma/dot ambiguity
    """
    aliases = {**DEFAULT_ALIASES, **(aliases or {})}
    universe = list(symbols) if symbols else list(FALLBACK_SYMBOLS)
    universe = [s.split(".")[0].split("#")[0] for s in universe]  # strip broker suffix

    sig = Signal(raw=text)
    t = _clean(text).upper()
    # "SL:\n2640" -> "SL: 2640"
    t = re.sub(r"\b(SL|TP\d?|ENTRY|EP)\s*[:=\-]?\s*\n\s*", r"\1 ", t)

    if not t.strip():
        return sig

    # ---- follow-up / management messages ---------------------------------- #
    symbol_in_msg = find_symbol(t, universe, aliases)
    m_be_pips = BE_PIPS_RE.search(t)

    if not DIRECTION_RE.search(t):
        # partial close: "close half", "book 50%", "take partial"
        mp = PARTIAL_RE.search(t)
        if mp:
            sig.action = "close_partial"
            sig.symbol = symbol_in_msg
            sig.fraction = _fraction(mp.group(1))
            if BE_RE.search(t):
                sig.be_pips = float(m_be_pips.group(1)) if m_be_pips else 0.0
                sig.notes.append("also move SL to BE")
            sig.confidence = "high"
            sig.notes.append(f"partial close {sig.fraction:.0%}")
            return sig

        # "entry missed", "cancel the order", "close pending orders"
        if (CANCEL_RE.search(t) or ENTRY_MISSED_RE.search(t)
                or (CLOSE_RE.search(t) and PENDING_RE.search(t)
                    and not CLOSE_ALL_RE.search(t))):
            sig.action = "cancel_pending"
            sig.symbol = symbol_in_msg
            sig.confidence = "high"
            sig.notes.append("cancel pending orders" +
                             (f" on {sig.symbol}" if sig.symbol else " (all symbols)"))
            return sig

        # "move SL to BE" / "BE now" / "SL to breakeven" / "Move SL to Entry"
        if BE_RE.search(t) or BE_ENTRY_RE.search(t):
            sig.action = "move_be"
            sig.symbol = symbol_in_msg
            sig.be_pips = float(m_be_pips.group(1)) if m_be_pips else None
            sig.confidence = "high"
            sig.notes.append("move SL to break-even" +
                             (f" (+{sig.be_pips:g} pips)" if sig.be_pips else ""))
            return sig

        if MODIFY_RE.search(t) or TRAIL_RE.search(t):
            sig.action = "unsupported"
            sig.symbol = symbol_in_msg
            sig.issues.append("management-only message; trailing/running rules run inside the "
                              "EA (InpTrail*), nothing to execute here")
            return sig

        if CLOSE_RE.search(t) and CLOSE_ALL_RE.search(t):
            sig.action = "close_all"
            sig.confidence = "high"
            sig.notes.append("close all positions")
            return sig

        if CLOSE_RE.search(t) and symbol_in_msg:
            sig.action = "close_symbol"
            sig.symbol = symbol_in_msg
            sig.confidence = "high"
            sig.notes.append(f"close positions on {sig.symbol}")
            return sig

    # plain chat (no numbers, no management keyword) -> nothing to parse
    management_hint = bool(MODIFY_VERB_RE.search(t) or CANCEL_RE.search(t) or CLOSE_RE.search(t)
                           or PARTIAL_RE.search(t) or BE_RE.search(t) or TRAIL_RE.search(t)
                           or ENTRY_MISSED_RE.search(t))
    # "GOLD BUY ENTER NOW" has no numbers at all but is still a trade signal
    order_hint = bool(DIRECTION_RE.search(t) and ORDERTYPE_RE.search(t))
    if not re.search(r"\d", t) and not management_hint and not order_hint:
        return sig

    # ---- target change: "Change All Sell Trades To TP 4135" --------------- #
    looks_like_trade = (len(TP_RE.findall(t)) >= 2            # TP1..TP7 list = a signal
                        or SL_RE.search(t)                     # SL/STOP LOSS present = a signal
                        or re.search(r"\bENTR(?:Y|IES)\b\s*[:=]", t))
    if (MODIFY_VERB_RE.search(t) and (TARGET_RE.search(t) or CHANGE_TO_BE_RE.search(t))
            and not STRUCTURED_ORDER_RE.search(t)
            and not looks_like_trade
            and not CANCEL_RE.search(t) and not PARTIAL_RE.search(t)):
        md = DIRECTION_RE.search(t)
        sig.direction = ("BUY" if md.group(1) in ("BUY", "LONG") else "SELL") if md else None
        sig.symbol = find_symbol(t, universe, aliases)
        sig.scope = "pending" if PENDING_SCOPE_RE.search(t) else "positions"

        if CHANGE_TO_BE_RE.search(t) or BE_RE.search(t):
            sig.action = "move_be"
            mpi = BE_PIPS_RE.search(t)
            sig.be_pips = float(mpi.group(1)) if mpi else None
            sig.confidence = "high"
            sig.notes.append(f"move SL to BE on {sig.scope} ({sig.direction or 'all directions'})")
            return sig

        nums = re.findall(NUM, t)
        if nums:
            val = choose_price(nums[-1], (hint_prices or {}).get(sig.symbol or ""))
            if val:
                sig.tp = val
                sig.action = "modify_tp"
                sig.confidence = "high"
                sig.notes.append(f"set TP of {sig.scope} ({sig.direction or 'all directions'}) to {val}")
                return sig

    # ---- symbol ----------------------------------------------------------- #
    sig.symbol = find_symbol(t, universe, aliases)

    # ---- direction -------------------------------------------------------- #
    m = DIRECTION_RE.search(t)
    if m:
        sig.direction = "BUY" if m.group(1) in ("BUY", "LONG") else "SELL"
    else:
        if any(e in text for e in EMOJI_BUY) and not any(e in text for e in EMOJI_SELL):
            sig.direction = "BUY"
            sig.issues.append("direction from emoji only")
        elif any(e in text for e in EMOJI_SELL) and not any(e in text for e in EMOJI_BUY):
            sig.direction = "SELL"
            sig.issues.append("direction from emoji only")

    # channel did not write the symbol (e.g. "SELL 4155-4160 / STOP LOST 4165")
    if not sig.symbol and default_symbol and sig.direction:
        sig.symbol = default_symbol
        sig.notes.append(f"no symbol written in the message -> using {default_symbol}")

    # ---- order type ------------------------------------------------------- #
    mt = None
    for cand in ORDERTYPE_RE.finditer(t):
        if cand.group(1) == "STOP" and re.match(r"\s*[_-]?\s*LOSS\b", t[cand.end():]):
            continue                                   # "STOP LOSS" is a stop-loss, not a stop order
        mt = cand
        break
    if mt:
        raw_type = mt.group(1)
        if raw_type in ("MARKET", "INSTANT", "NOW"):
            sig.order_type = "MARKET"
        else:
            sig.order_type = raw_type          # LIMIT / STOP
    else:
        sig.order_type = default_order_type.upper()
        sig.issues.append(f"no LIMIT/STOP keyword, assumed {sig.order_type}")

    # a message with neither a direction nor an order keyword is just chat/commentary
    if sig.direction is None and mt is None:
        sig.action = "ignore"
        return sig

    # ---- lot size --------------------------------------------------------- #
    ml = LOT_RE.search(t) or LOT_INLINE_RE.search(t)
    if ml:
        v = choose_price(ml.group(1))
        if v and 0.001 <= v <= 100:
            sig.volume = v

    # ---- strip noise + SL/TP so only the entry price is left -------------- #
    body = t
    msl = SL_RE.search(body)
    if msl:
        blob = msl.group("val")
        if blob:
            vals = [choose_price(v, (hint_prices or {}).get(sig.symbol or "")) for v in _split_values(blob)]
            vals = [v for v in vals if v]
            if vals:
                sig.sl = vals[0]
        else:
            pips_txt = msl.group("pips")
            pips = float(re.sub(r"[^\d.]", "", pips_txt.replace(",", ".")))
            sig.notes.append(f"SL given in pips ({pips:g})")
            sig.sl = ("PIPS", pips)  # resolved after entry is known
        body = body[:msl.start()] + " " + body[msl.end():]
    else:
        sig.issues.append("no stop loss found")

    tps: List[float] = []
    tps_pips: List[float] = []
    for mtp in list(TP_RE.finditer(body)):
        if mtp.group("val"):
            for v in _split_values(mtp.group("val")):
                p = choose_price(v, (hint_prices or {}).get(sig.symbol or ""))
                if p:
                    tps.append(p)
        elif mtp.group("pips"):
            tps_pips.append(float(re.sub(r"[^\d.]", "", mtp.group("pips").replace(",", "."))))
        body = body[:mtp.start()] + " " + body[mtp.end():]

    for nz in NOISE_RES:
        body = nz.sub(" ", body)
    if sig.volume is not None:
        body = LOT_RE.sub(" ", body)
        body = LOT_INLINE_RE.sub(" ", body)

    # ---- entry price ------------------------------------------------------ #
    entry_raw: List[str] = []
    used_pattern = None

    # One channel writes a two-price entry zone with a space, e.g. "SELL 4173 4177".
    # Accept that as a range only when both prices are plausible and close enough
    # to be a zone; this avoids reading a pip count or unrelated number as an entry.
    m_space_range = SPACE_RANGE_AFTER_DIRECTION_RE.search(body)
    if m_space_range:
        range_hint = (hint_prices or {}).get(sig.symbol or "")
        p1 = choose_price(m_space_range.group(1), range_hint)
        p2 = choose_price(m_space_range.group(2), range_hint)
        if (p1 and p2 and p1 != p2
                and plausible_price(sig.symbol, p1, range_hint)
                and plausible_price(sig.symbol, p2, range_hint)
                and 0.8 <= p2 / p1 <= 1.2):
            entry_raw = [m_space_range.group(1), m_space_range.group(2)]
            used_pattern = -1
            sig.notes.append("space-separated prices after BUY/SELL treated as an entry range")

    if not entry_raw:
        for i, pat in enumerate(ENTRY_PATTERNS):
            m2 = pat.search(body)
            if m2:
                entry_raw = _split_values(m2.group(1))
                used_pattern = i
                break
    if not entry_raw and positional_fallback:
        rest = re.findall(NUM, body)
        # ignore bare small numbers that look like a lot size / year
        rest = [r for r in rest if not re.fullmatch(r"20\d{2}", r.strip()) or len(re.findall(NUM, body)) == 1]
        if rest:
            entry_raw = [rest[0]]
            used_pattern = 99

    hint = (hint_prices or {}).get(sig.symbol or "")
    entries: List[float] = []
    for tok in entry_raw:
        p = choose_price(tok, hint)
        if not p or p in entries:
            continue
        # guard against reaction counts / lot sizes / years being read as a price
        if not plausible_price(sig.symbol, p, hint):
            sig.issues.append(f"ignored implausible price {p:g}")
            continue
        entries.append(p)
    if used_pattern == 99 and entries:
        sig.issues.append("entry price found only by position - check it")
    # "marked" = the message used an explicit entry marker (ENTER IN / ENTRY: / @ price),
    # not a bare number after BUY/SELL (which in market channels is just the live price)
    sig.entry_marked = (used_pattern in (0, 1, 2) and bool(entries))
    sig.entries = entries

    # resolve pip-based SL/TP now that we have an entry
    ref = entries[0] if entries else None
    if ref and isinstance(sig.sl, tuple):
        _, pips = sig.sl
        step = pip_size_for(sig.symbol or "", pip_sizes) * pips
        sig.sl = ref - step if sig.direction == "BUY" else ref + step
    elif sig.sl is not None and not isinstance(sig.sl, float):
        sig.sl = None
    if ref and tps_pips:
        step_default = pip_size_for(sig.symbol or "", pip_sizes)
        for pips in tps_pips:
            tps.append(ref + step_default * pips if sig.direction == "BUY" else ref - step_default * pips)

    # sort TPs sensibly (nearest first)
    if ref and sig.direction == "BUY":
        sig.tps = sorted([x for x in tps if x > ref]) or tps
    elif ref and sig.direction == "SELL":
        sig.tps = sorted([x for x in tps if x < ref], reverse=True) or tps
    else:
        sig.tps = tps

    # ---- direction sanity: the SL / TP prices are stronger evidence than the
    #      word BUY or SELL (channels sometimes type the wrong one) ---------- #
    if fix_direction and sig.sl and sig.entries and sig.direction:
        ref = float(sig.entries[0])
        wrong_side = ((sig.direction == "BUY" and sig.sl > ref) or
                      (sig.direction == "SELL" and sig.sl < ref))
        if wrong_side:
            flipped = "SELL" if sig.direction == "BUY" else "BUY"
            tps_ok = True
            if tps:
                tps_ok = (all(t < ref for t in tps) if flipped == "SELL"
                          else all(t > ref for t in tps))
            if tps_ok:
                sig.issues.append(f"the message said {sig.direction} but the SL/TP say "
                                  f"{flipped} -> using {flipped}")
                sig.direction = flipped

    # ---- sanity / confidence ---------------------------------------------- #
    if not sig.symbol:
        sig.issues.append("no symbol recognised")
    if not sig.direction:
        sig.issues.append("no BUY/SELL direction")
    if not sig.entries and sig.order_type != "MARKET":
        sig.issues.append("no entry price found")

    if ref and sig.sl:
        if sig.direction == "BUY" and sig.sl >= ref:
            sig.issues.append("SL is above entry for a BUY - check the signal")
        if sig.direction == "SELL" and sig.sl <= ref:
            sig.issues.append("SL is below entry for a SELL - check the signal")

    blocking = not sig.symbol or not sig.direction or (not sig.entries and sig.order_type != "MARKET")
    if blocking:
        sig.confidence = "low"
    elif any("check" in i or "only" in i or "assumed" in i or "emoji" in i for i in sig.issues):
        sig.confidence = "medium"
    else:
        sig.confidence = "high"

    # Guard against status recaps being promoted into fresh entries. A result update
    # needs explicit entry context before it can be treated as a new signal.
    outcome_update = bool(OUTCOME_WORD_RE.search(t) and OUTCOME_METRIC_RE.search(t))
    explicit_order_text = bool(
        STRUCTURED_ORDER_RE.search(t)
        or re.search(
            r"\b(?:(?:BUY|SELL|LONG|SHORT)\s+(?:NOW|MARKET|INSTANT)"
            r"|(?:NOW|MARKET|INSTANT)\s+(?:BUY|SELL|LONG|SHORT)|ENTER\s+NOW)\b", t)
    )
    has_text_direction = bool(DIRECTION_RE.search(t))
    fresh_entry_structure = has_text_direction and (
        sig.entry_marked or explicit_order_text or
        (bool(sig.entries) and sig.sl is not None and bool(sig.tps))
    )

    # Emoji + a positional number alone is especially ambiguous (as in a TP
    # recap); don't let market-channel defaults turn it into an order.
    emoji_positional_fallback = (
        "direction from emoji only" in sig.issues
        and "entry price found only by position - check it" in sig.issues
        and not symbol_in_msg
        and sig.sl is None and not sig.tps
        and not sig.entry_marked
    )

    ignore_reasons = []
    if outcome_update and not fresh_entry_structure:
        ignore_reasons.append(
            "looks like a TP/result or pips-progress update, not a clearly marked fresh entry"
        )
    if emoji_positional_fallback:
        ignore_reasons.append(
            "emoji-only direction plus a positional price has no explicit symbol, SL/TP, or entry cue"
        )
    if ignore_reasons:
        sig.action = "ignore"
        sig.confidence = "high"
        sig.notes.extend(ignore_reasons)
        return sig

    # "After Hit TP1, Move SL to Entry" -> group BE once a TP is hit
    if BE_AFTER_TP1_RE.search(t) and (BE_RE.search(t) or BE_ENTRY_RE.search(t)):
        sig.be_after_tp1 = True
        sig.notes.append("channel asks BE after TP1 -> EA moves remaining trades to BE")

    # "BE on 70 Pips" hint line -> the EA can move SL to BE at +70 pips
    if m_be_pips:
        sig.be_pips = float(m_be_pips.group(1))
        sig.notes.append(f"channel advises BE at +{sig.be_pips:g} pips")

    sig.action = "place"
    return sig
