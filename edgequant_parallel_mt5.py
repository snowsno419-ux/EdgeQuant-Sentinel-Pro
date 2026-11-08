"""Independent MT5 subprocess fan-out for EdgeQuant Sentinel.

Each job has ONE broker and a separate Python process. Only public broker
metadata and the parsed signal cross stdin; passwords remain in the Windows
DPAPI vault and are read only by the intended worker under that user's login.

This is simultaneous *submission*, not a guarantee of equal broker fills.
"""
from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

RESULT_PREFIX = "EDGEQUANT_PARALLEL_RESULT="
MAX_OUTPUT = 1024 * 1024
WORKER_TIMEOUT_SECONDS = 75


def _run_one(engine_file: Path, job: dict, *, python_executable=None, timeout=WORKER_TIMEOUT_SECONDS,
             runner=None) -> dict:
    name = str(job.get("broker") or "")
    runner = runner or subprocess.run
    command = [str(python_executable or sys.executable), "-u", str(engine_file), "--parallel-mt5-worker"]
    try:
        complete = runner(command, input=json.dumps(job, ensure_ascii=False), text=True,
                          encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout, cwd=str(engine_file.parent))
    except subprocess.TimeoutExpired:
        # Timeout may be AFTER broker accepted the order. Never retry this job.
        return {"broker": name, "status": "uncertain", "error": "worker timed out; check MT5 broker history; no retry"}
    except (OSError, ValueError) as exc:
        return {"broker": name, "status": "failed", "error": "worker did not start: " + type(exc).__name__}
    output = (complete.stdout or "")[-MAX_OUTPUT:]
    for line in reversed(output.splitlines()):
        if line.startswith(RESULT_PREFIX):
            try:
                result = json.loads(line[len(RESULT_PREFIX):])
                if isinstance(result, dict) and result.get("broker") == name:
                    return result
            except (ValueError, TypeError):
                break
    # On crash, the worker may have sent an order and failed before reporting.
    return {"broker": name, "status": "uncertain",
            "error": "worker exited without a valid receipt; inspect MT5 order history; no retry"}


def dispatch_all(engine_file: Path, jobs: list, *, python_executable=None, timeout=WORKER_TIMEOUT_SECONDS,
                 runner=None) -> list:
    """Launch ALL accounts before awaiting any result; preserve target ordering."""
    if not jobs:
        return []
    engine_file = Path(engine_file)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs), thread_name_prefix="mt5-broker") as pool:
        futures = [pool.submit(_run_one, engine_file, job, python_executable=python_executable,
                               timeout=timeout, runner=runner) for job in jobs]
        output = []
        for job, future in zip(jobs, futures):
            try:
                output.append(future.result())
            except Exception as exc:
                output.append({"broker": job.get("broker"), "status": "uncertain",
                               "error": "unexpected worker error; broker outcome uncertain: " + type(exc).__name__})
        return output
