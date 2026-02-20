#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUN_SINGLE = ROOT / "scripts" / "bench" / "run_graph_regime_universe.py"


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _slug(text: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(text))
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "asset"


def _read_tickers(tickers: str, tickers_file: str) -> list[str]:
    out: list[str] = []
    if tickers.strip():
        out.extend([x.strip() for x in tickers.split(",") if x.strip()])
    if tickers_file.strip():
        p = Path(tickers_file)
        if p.exists():
            out.extend([x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()])
    uniq: list[str] = []
    seen: set[str] = set()
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _copy_artifacts(run_dir: Path, outdir: Path, ticker: str, timeframes: list[str]) -> None:
    src_assets = run_dir / "assets"
    dst_assets = outdir / "assets"
    dst_assets.mkdir(parents=True, exist_ok=True)
    if not src_assets.exists():
        return
    for tf in timeframes:
        prefix = f"{ticker}_{tf}"
        for p in src_assets.glob(f"{prefix}*"):
            target = dst_assets / p.name
            if p.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(p, target)
            else:
                shutil.copy2(p, target)


def _load_universe_rows(run_dir: Path, tf: str) -> list[dict[str, Any]]:
    p = run_dir / f"universe_{tf}.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _already_done(outdir: Path, ticker: str, timeframes: list[str]) -> bool:
    assets_dir = outdir / "assets"
    if not assets_dir.exists():
        return False
    for tf in timeframes:
        if not (assets_dir / f"{ticker}_{tf}.json").exists():
            return False
    return True


def _has_min_asset_output(run_dir: Path, ticker: str, timeframes: list[str]) -> bool:
    assets_dir = run_dir / "assets"
    if not assets_dir.exists():
        return False
    for tf in timeframes:
        if not (assets_dir / f"{ticker}_{tf}.json").exists():
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Robust batch runner for graph universe with resume support.")
    ap.add_argument("--tickers", type=str, default="")
    ap.add_argument("--tickers-file", type=str, default="")
    ap.add_argument("--timeframes", type=str, default="daily")
    ap.add_argument("--outdir", type=str, default="")
    ap.add_argument("--mode", type=str, default="fast", choices=["fast", "heavy"])
    ap.add_argument("--n-micro", type=int, default=0)
    ap.add_argument("--n-regimes", type=int, default=0)
    ap.add_argument("--k-nn", type=int, default=0)
    ap.add_argument("--theiler", type=int, default=0)
    ap.add_argument("--alpha", type=float, default=0.0)
    ap.add_argument("--micro-method", type=str, default="")
    ap.add_argument("--metastable-method", type=str, default="")
    ap.add_argument("--max-assets", type=int, default=0)
    ap.add_argument("--start-index", type=int, default=0)
    ap.add_argument("--resume", type=int, default=1)
    ap.add_argument("--timeout-sec", type=int, default=180)
    ap.add_argument("--stop-on-fail", type=int, default=0)
    args = ap.parse_args()

    tickers = _read_tickers(args.tickers, args.tickers_file)
    if not tickers:
        raise SystemExit("no tickers provided")
    if int(args.start_index) > 0:
        tickers = tickers[int(args.start_index) :]
    if int(args.max_assets) > 0:
        tickers = tickers[: int(args.max_assets)]
    if not tickers:
        raise SystemExit("empty ticker list after slicing")

    timeframes = [x.strip() for x in str(args.timeframes).split(",") if x.strip()]
    run_id = _now_id()
    outdir = Path(args.outdir) if args.outdir else (ROOT / "results" / f"latest_graph_universe_batch_{run_id}")
    runs_dir = outdir / "_runs"
    outdir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    merged: dict[str, dict[str, dict[str, Any]]] = {tf: {} for tf in timeframes}
    logs: list[dict[str, Any]] = []
    n_ok = 0
    n_fail = 0

    mpl_cache = outdir / "_mplconfig"
    mpl_cache.mkdir(parents=True, exist_ok=True)
    base_env = os.environ.copy()
    base_env["MPLCONFIGDIR"] = str(mpl_cache)
    base_env["LOKY_MAX_CPU_COUNT"] = str(base_env.get("LOKY_MAX_CPU_COUNT", "4"))
    base_env["OMP_NUM_THREADS"] = str(base_env.get("OMP_NUM_THREADS", "1"))
    base_env["OPENBLAS_NUM_THREADS"] = str(base_env.get("OPENBLAS_NUM_THREADS", "1"))
    base_env["MKL_NUM_THREADS"] = str(base_env.get("MKL_NUM_THREADS", "1"))
    base_env["NUMEXPR_NUM_THREADS"] = str(base_env.get("NUMEXPR_NUM_THREADS", "1"))

    for i, ticker in enumerate(tickers, start=1):
        global_idx = int(args.start_index) + i
        print(f"[batch] {global_idx}/{int(args.start_index) + len(tickers)} ticker={ticker} start", flush=True)
        if int(args.resume) == 1 and _already_done(outdir=outdir, ticker=ticker, timeframes=timeframes):
            logs.append({"ticker": ticker, "status": "skip_resume", "index": global_idx})
            print(f"[batch] {global_idx}/{int(args.start_index) + len(tickers)} ticker={ticker} skip_resume", flush=True)
            continue

        run_dir = runs_dir / f"{global_idx:04d}_{_slug(ticker)}"
        cmd = [
            sys.executable,
            str(RUN_SINGLE),
            "--tickers",
            ticker,
            "--timeframes",
            ",".join(timeframes),
            "--outdir",
            str(run_dir),
            "--mode",
            str(args.mode),
        ]
        if int(args.n_micro) > 0:
            cmd += ["--n-micro", str(int(args.n_micro))]
        if int(args.n_regimes) > 0:
            cmd += ["--n-regimes", str(int(args.n_regimes))]
        if int(args.k_nn) > 0:
            cmd += ["--k-nn", str(int(args.k_nn))]
        if int(args.theiler) > 0:
            cmd += ["--theiler", str(int(args.theiler))]
        if float(args.alpha) > 0:
            cmd += ["--alpha", str(float(args.alpha))]
        if str(args.micro_method).strip():
            cmd += ["--micro-method", str(args.micro_method).strip()]
        if str(args.metastable_method).strip():
            cmd += ["--metastable-method", str(args.metastable_method).strip()]

        try:
            proc = subprocess.run(
                cmd,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=max(1, int(args.timeout_sec)),
                env=base_env,
            )
            tail = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")).strip()[-3000:]
            code = int(proc.returncode)
        except subprocess.TimeoutExpired as exc:
            code = 124
            tail = f"timeout after {int(args.timeout_sec)}s: {exc}"

        has_output = _has_min_asset_output(run_dir=run_dir, ticker=ticker, timeframes=timeframes)
        if code != 0 and not has_output:
            n_fail += 1
            logs.append({"ticker": ticker, "status": "fail", "index": global_idx, "code": code, "tail": tail})
            print(f"[batch] {global_idx}/{int(args.start_index) + len(tickers)} ticker={ticker} fail code={code}", flush=True)
            if int(args.stop_on_fail) == 1:
                break
            continue

        _copy_artifacts(run_dir=run_dir, outdir=outdir, ticker=ticker, timeframes=timeframes)
        for tf in timeframes:
            for row in _load_universe_rows(run_dir=run_dir, tf=tf):
                asset = str(row.get("asset", "")).strip()
                timeframe = str(row.get("timeframe", tf)).strip()
                if not asset:
                    continue
                merged[tf][f"{asset}|{timeframe}"] = row
        n_ok += 1
        if code == 0:
            logs.append({"ticker": ticker, "status": "ok", "index": global_idx, "code": 0})
            print(f"[batch] {global_idx}/{int(args.start_index) + len(tickers)} ticker={ticker} ok", flush=True)
        else:
            logs.append(
                {
                    "ticker": ticker,
                    "status": "ok_salvaged",
                    "index": global_idx,
                    "code": code,
                    "tail": tail,
                }
            )
            print(f"[batch] {global_idx}/{int(args.start_index) + len(tickers)} ticker={ticker} ok_salvaged code={code}", flush=True)

    for tf in timeframes:
        rows = list(merged[tf].values())
        rows.sort(key=lambda r: (str(r.get("asset", "")), str(r.get("timeframe", ""))))
        (outdir / f"universe_{tf}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    fallback_counts = {}
    assets_dir = outdir / "assets"
    for tf in timeframes:
        fallback_counts[tf] = int(len(list(assets_dir.glob(f"*_{tf}.json")))) if assets_dir.exists() else 0
    computed_counts = {tf: int(len(merged[tf])) for tf in timeframes}
    final_counts = {tf: (computed_counts[tf] if computed_counts[tf] > 0 else fallback_counts[tf]) for tf in timeframes}

    summary = {
        "status": "ok" if n_fail == 0 else "partial",
        "run_id": run_id,
        "outdir": str(outdir),
        "n_requested": int(len(tickers)),
        "n_ok": int(n_ok),
        "n_fail": int(n_fail),
        "timeframes": timeframes,
        "universe_counts": final_counts,
    }
    (outdir / "batch_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "batch_log.json").write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

    if n_fail > 0 and int(args.stop_on_fail) == 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
