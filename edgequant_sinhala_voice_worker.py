#!/usr/bin/env python3
"""Private, offline worker for the optional Sinhala female VITS voice.

The worker accepts short JSON files from EdgeQuant in the user's LOCALAPPDATA
queue directory. It binds no network port and does not transmit report text.
The model/runtime are installed separately with INSTALL-SINHALA-FEMALE-VOICE.bat.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import traceback
import urllib.request
import uuid
from pathlib import Path

MODEL_REPO = "https://huggingface.co/dialoglk/SinhalaVITS-TTS-F1/resolve/main/"
MODEL_FILES = {
    "Nipunika_210000.pth": MODEL_REPO + "Nipunika_210000.pth?download=true",
    "Nipunika_config.json": MODEL_REPO + "Nipunika_config.json?download=true",
    "romanizer.py": MODEL_REPO + "romanizer.py?download=true",
}
TEST_TEXT = ("ආයුබෝවන්. අද ඔබගේ ගිණුමේ ශේෂය ඇමරිකානු ඩොලර් 1,000.00යි. "
             "විවෘත ගනුදෙනුවල තාවකාලික ලාභය 12.50යි.")


_SI_ONES = {
    0: "බිංදුව", 1: "එක", 2: "දෙක", 3: "තුන", 4: "හතර", 5: "පහ",
    6: "හය", 7: "හත", 8: "අට", 9: "නවය", 10: "දහය",
    11: "එකොළහ", 12: "දොළහ", 13: "දහතුන", 14: "දාහතර",
    15: "පහළොව", 16: "දහසය", 17: "දහහත", 18: "දහඅට", 19: "දහනවය",
}
_SI_TENS = {2: "විසි", 3: "තිස්", 4: "හතළිස්", 5: "පනස්",
            6: "හැට", 7: "හැත්තෑ", 8: "අසූ", 9: "අනූ"}
_SI_TENS_EXACT = {20: "විස්ස", 30: "තිහ", 40: "හතළිහ", 50: "පනහ",
                  60: "හැට", 70: "හැත්තෑව", 80: "අසූව", 90: "අනූව"}
_SI_HUNDREDS = {1: "එකසිය", 2: "දෙසිය", 3: "තුන්සිය", 4: "හාරසිය",
                5: "පන්සිය", 6: "හයසිය", 7: "හත්සිය", 8: "අටසිය", 9: "නවසිය"}
_SI_DIGITS = ("බිංදුව", "එක", "දෙක", "තුන", "හතර", "පහ", "හය", "හත", "අට", "නවය")
_NUMBER_RE = re.compile(r"(?<!\w)([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?!\w)")
_TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)")


def _sinhala_under_100(value: int) -> str:
    if value < 20:
        return _SI_ONES[value]
    if value in _SI_TENS_EXACT:
        return _SI_TENS_EXACT[value]
    tens, ones = divmod(value, 10)
    return _SI_TENS.get(tens, "") + (" " + _SI_ONES[ones] if ones else "")


def sinhala_integer_words(value: int) -> str:
    """Speak an integer in Sinhala words, avoiding unsupported model digits."""
    value = abs(int(value))
    if value < 100:
        return _sinhala_under_100(value)
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        return _SI_HUNDREDS[hundreds] + (" " + _sinhala_under_100(rest) if rest else "")
    pieces = []
    for unit, label in ((1_000_000_000, "බිලියන"),
                        (1_000_000, "මිලියන"), (1000, "දහස්")):
        count, value = divmod(value, unit)
        if count:
            spoken_count = "එක්" if count == 1 else sinhala_integer_words(count)
            spoken_label = ("දහස" if unit == 1000 and count == 1 and value == 0 else label)
            pieces.extend((spoken_count, spoken_label))
    if value:
        pieces.append(sinhala_integer_words(value))
    return " ".join(pieces) if pieces else _SI_ONES[0]


def _number_to_sinhala(match: re.Match) -> str:
    raw = match.group(1)
    negative = raw.startswith("-")
    raw = raw.lstrip("+-").replace(",", "")
    whole, dot, fraction = raw.partition(".")
    spoken = sinhala_integer_words(int(whole or "0"))
    if dot:
        # Say fractional digits individually so 2.05 remains distinct from 2.5.
        spoken += " දශම " + " ".join(_SI_DIGITS[int(digit)] for digit in fraction)
    return ("අඩු " if negative else "") + spoken


def expand_dynamic_text(text: str) -> str:
    """Expand times, numbers, currency and trading acronyms for this model's alphabet."""
    value = str(text or "")
    value = re.sub(r"\bXAUUSD\b", "ගෝල්ඩ්", value, flags=re.IGNORECASE)
    value = re.sub(r"\bUSD\b", "ඇමරිකානු ඩොලර්", value, flags=re.IGNORECASE)
    value = re.sub(r"\bMT5\b", "එම් ටී පහ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bTP\b", "ටී පී", value, flags=re.IGNORECASE)
    value = re.sub(r"\bSL\b", "එස් එල්", value, flags=re.IGNORECASE)
    value = re.sub(r"\bBE\b", "බී ඊ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bP&L\b", "ලාභ අලාභ", value, flags=re.IGNORECASE)

    def spoken_time(match: re.Match) -> str:
        hour, minute, second = match.groups()
        parts = ["පැය", sinhala_integer_words(int(hour)),
                 "මිනිත්තු", sinhala_integer_words(int(minute))]
        if second is not None:
            parts.extend(("තත්පර", sinhala_integer_words(int(second))))
        return " ".join(parts)

    value = _TIME_RE.sub(spoken_time, value)
    value = re.sub(r"([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*%",
                   r"සියයට \1", value)
    value = _NUMBER_RE.sub(_number_to_sinhala, value)
    # Defensive pass: never let a digit reach a vocabulary that has no digits.
    return re.sub(r"\d", lambda match: _SI_DIGITS[int(match.group())], value)


def prepare_model_text(text: str, romanize, allowed_chars: str) -> str:
    """Romanize Sinhala and keep only the single-speaker checkpoint vocabulary."""
    roman = str(romanize(expand_dynamic_text(text)) or "").lower()
    # The published F1 vocabulary omits q, w, x, and z; use close pronounceable
    # equivalents so Latin channel/symbol names do not become unsupported IDs.
    roman = roman.translate(str.maketrans({"q": "k", "w": "v", "x": "ks", "z": "s"}))
    allowed = set(allowed_chars or " !'(),-.:;=?abcdefghijklmnoprstuvyæñāēīōśşūǣḍḥḷṁṅṇṉṛṝṭ")
    safe = "".join(ch if ch in allowed else " " for ch in roman)
    return re.sub(r"\s+", " ", safe).strip()


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def _download(url: str, target: Path) -> None:
    """Download with resume support, visible progress, and an atomic final name."""
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    offset = part.stat().st_size if part.exists() else 0
    headers = {"User-Agent": "EdgeQuant-Sinhala-Female-Voice/1.0"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        status = getattr(response, "status", response.getcode())
        if offset and status != 206:
            offset = 0
        length = int(response.headers.get("Content-Length") or 0)
        total = offset + length if length else 0
        mode = "ab" if offset and status == 206 else "wb"
        done = offset
        last_report = 0
        with part.open(mode) as fh:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                fh.write(block)
                done += len(block)
                if done - last_report >= 16 * 1024 * 1024:
                    if total:
                        pct = min(100.0, 100.0 * done / total)
                        print(f"  {target.name}: {done / (1024*1024):,.0f} MB  ({pct:.0f}%)",
                              flush=True)
                    else:
                        print(f"  {target.name}: {done / (1024*1024):,.0f} MB",
                              flush=True)
                    last_report = done
    if target.name == "Nipunika_210000.pth" and part.stat().st_size < 100_000_000:
        raise RuntimeError("The female Sinhala VITS checkpoint download is incomplete (<100 MB).")
    if target.name.endswith(".json") and part.stat().st_size < 100:
        raise RuntimeError(f"The model config download looks incomplete: {target.name}")
    part.replace(target)
    print(f"  saved {target.name} ({target.stat().st_size / (1024*1024):,.1f} MB)", flush=True)


def install_model(model_dir: Path) -> None:
    print("Downloading the local Sinhala female voice files from Dialog/UoM's public model.",
          flush=True)
    for filename, url in MODEL_FILES.items():
        target = model_dir / filename
        if target.exists() and (target.stat().st_size > 100 if filename.endswith(".json")
                                or filename.endswith(".py") else
                                target.stat().st_size > 100_000_000):
            print(f"  already present: {filename}", flush=True)
            continue
        _download(url, target)
    notice = model_dir / "MODEL-NOTICE.txt"
    notice.write_text(
        "Optional local Sinhala female voice model\n"
        "Model: dialoglk/SinhalaVITS-TTS-F1 (female speaker Nipunika)\n"
        "Publisher: Dialog Axiata PLC and Dialog-University of Moratuwa Research Lab\n"
        "Model card/license: https://huggingface.co/dialoglk/SinhalaVITS-TTS-F1\n"
        "The model card declares MPL-2.0. Review the model card before redistribution.\n"
        "EdgeQuant uses the model locally. Signal/report text is not uploaded.\n",
        encoding="utf-8")


def _load_synthesizer(model_dir: Path):
    if not (model_dir / "Nipunika_210000.pth").is_file():
        raise FileNotFoundError("Female VITS checkpoint is missing; run the installer first.")
    if not (model_dir / "Nipunika_config.json").is_file():
        raise FileNotFoundError("Female VITS config is missing; run the installer first.")
    sys.path.insert(0, str(model_dir))
    from romanizer import sinhala_to_roman
    from TTS.utils.synthesizer import Synthesizer
    config_data = json.loads((model_dir / "Nipunika_config.json").read_text(encoding="utf-8"))
    characters = str(((config_data.get("characters") or {}).get("characters") or ""))
    if not characters:
        raise ValueError("The model config contains no character vocabulary.")
    synthesizer = Synthesizer(
        tts_checkpoint=str(model_dir / "Nipunika_210000.pth"),
        tts_config_path=str(model_dir / "Nipunika_config.json"),
        use_cuda=False,
    )
    return synthesizer, sinhala_to_roman, characters


def _synthesize(synthesizer, romanize, allowed_chars: str, text: str, output: Path) -> None:
    import numpy as np

    # Break a long report into sentence-sized segments to reduce CPU latency and
    # give the female voice natural pauses; keep all report content in order.
    parts = [x.strip() for x in re.split(r"(?<=[.!?।])\s+", text.strip()) if x.strip()]
    if not parts:
        raise ValueError("There is no report text to speak.")
    rate = int(getattr(synthesizer, "output_sample_rate", 22050) or 22050)
    silence = np.zeros(max(1, int(rate * 0.20)), dtype=np.float32)
    waves = []
    for sentence in parts:
        model_text = prepare_model_text(sentence, romanize, allowed_chars)
        if not model_text:
            continue
        samples = np.asarray(synthesizer.tts(model_text), dtype=np.float32).reshape(-1)
        if samples.size:
            waves.extend((samples, silence))
    if not waves:
        raise RuntimeError("The voice model returned an empty recording.")
    output.parent.mkdir(parents=True, exist_ok=True)
    synthesizer.save_wav(np.concatenate(waves), str(output))


def test_model(model_dir: Path, play: bool = True) -> None:
    synthesizer, romanize, allowed_chars = _load_synthesizer(model_dir)
    output = Path(tempfile.gettempdir()) / f"edgequant_sinhala_voice_test_{os.getpid()}.wav"
    _synthesize(synthesizer, romanize, allowed_chars, TEST_TEXT, output)
    print(f"Female Sinhala voice test created: {output}", flush=True)
    if play:
        if os.name != "nt":
            raise RuntimeError("Audio playback verification is supported on Windows only.")
        import winsound
        winsound.PlaySound(str(output), winsound.SND_FILENAME)
        try:
            output.unlink()
        except OSError:
            pass
    print("Offline female Sinhala voice test completed.", flush=True)


def _serve(model_dir: Path, queue_dir: Path) -> int:
    requests_dir = queue_dir / "requests"
    results_dir = queue_dir / "results"
    audio_dir = queue_dir / "audio"
    for folder in (requests_dir, results_dir, audio_dir):
        folder.mkdir(parents=True, exist_ok=True)
    status_path = queue_dir / "status.json"
    stop_path = queue_dir / "STOP"
    _atomic_json(status_path, {"state": "starting", "ts": time.time(), "error": ""})
    try:
        synthesizer, romanize, allowed_chars = _load_synthesizer(model_dir)
    except Exception as exc:
        _atomic_json(status_path, {"state": "error", "ts": time.time(),
                                   "error": f"{type(exc).__name__}: {exc}"})
        (queue_dir / "worker.log").write_text(traceback.format_exc(), encoding="utf-8")
        return 2
    _atomic_json(status_path, {"state": "ready", "ts": time.time(), "error": ""})
    while True:
        files = sorted(requests_dir.glob("*.json"), key=lambda x: x.name)
        if stop_path.exists() and not files:
            break
        if not files:
            time.sleep(0.20)
            continue
        request_file = files[0]
        processing_file = request_file.with_suffix(".processing")
        try:
            request_file.replace(processing_file)
        except OSError:
            time.sleep(0.05)
            continue
        request_id = processing_file.stem
        audio_path = audio_dir / f"{request_id}.wav"
        result_path = results_dir / f"{request_id}.json"
        try:
            request_data = json.loads(processing_file.read_text(encoding="utf-8"))
            text = str(request_data.get("text") or "").strip()[:7000]
            created = float(request_data.get("created_ts") or time.time())
            if time.time() - created > 10 * 60:
                raise TimeoutError("Voice request expired before playback; press Read Report again.")
            _synthesize(synthesizer, romanize, allowed_chars, text, audio_path)
            if os.name != "nt":
                raise RuntimeError("Windows audio playback is unavailable on this platform.")
            import winsound
            # Synchronous playback serializes concurrent report/order messages.
            winsound.PlaySound(str(audio_path), winsound.SND_FILENAME)
            result = {"ok": True, "state": "played", "id": request_id,
                      "request_id": request_id, "ts": time.time()}
        except Exception as exc:
            result = {"ok": False, "state": "error", "id": request_id,
                      "request_id": request_id,
                      "error": f"{type(exc).__name__}: {exc}", "ts": time.time()}
            _atomic_json(status_path, {"state": "error", "ts": time.time(),
                                       "error": result["error"]})
        finally:
            try:
                processing_file.unlink()
            except OSError:
                pass
            try:
                audio_path.unlink()
            except OSError:
                pass
        _atomic_json(result_path, result)
        if result.get("ok"):
            _atomic_json(status_path, {"state": "ready", "ts": time.time(), "error": ""})
    try:
        stop_path.unlink()
    except OSError:
        pass
    _atomic_json(status_path, {"state": "stopped", "ts": time.time(), "error": ""})
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--install", action="store_true", help="download the optional local model")
    parser.add_argument("--test", action="store_true", help="synthesize and play a female voice test")
    parser.add_argument("--serve", action="store_true", help="run the private local file-queue worker")
    parser.add_argument("--queue-dir", type=Path, help="private queue directory under LOCALAPPDATA")
    args = parser.parse_args(argv)
    try:
        if args.install:
            install_model(args.model_dir)
            return 0
        if args.test:
            test_model(args.model_dir, play=True)
            return 0
        if args.serve:
            if not args.queue_dir:
                parser.error("--queue-dir is required with --serve")
            return _serve(args.model_dir, args.queue_dir)
        parser.error("choose --install, --test, or --serve")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
