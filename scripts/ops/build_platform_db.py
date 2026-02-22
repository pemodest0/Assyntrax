#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            continue
    return rows


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        n = float(value)
        if n == n and n not in {float("inf"), float("-inf")}:
            return n
    except Exception:
        pass
    return default


def _to_text(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_run_id(run_id_arg: str | None) -> str:
    if run_id_arg:
        return run_id_arg
    snapshots_root = ROOT / "results" / "ops" / "snapshots"
    dirs = sorted([p for p in snapshots_root.iterdir() if p.is_dir()], reverse=True)
    if not dirs:
        raise RuntimeError("nenhum run encontrado em results/ops/snapshots.")
    for run_dir in dirs:
        summary = _read_json(run_dir / "summary.json", {})
        status = _to_text(summary.get("status"), "").lower()
        gate = summary.get("deployment_gate") if isinstance(summary, dict) else {}
        blocked = bool(gate.get("blocked", False)) if isinstance(gate, dict) else False
        if status == "ok" and not blocked:
            return run_dir.name
    return dirs[0].name


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            gate_blocked INTEGER NOT NULL,
            gate_reasons_json TEXT NOT NULL,
            n_assets INTEGER NOT NULL,
            validated_signals INTEGER NOT NULL,
            watch_signals INTEGER NOT NULL,
            inconclusive_signals INTEGER NOT NULL,
            validated_ratio REAL NOT NULL,
            policy_path TEXT,
            official_window REAL,
            summary_path TEXT NOT NULL,
            snapshot_path TEXT NOT NULL,
            indexed_at_utc TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS asset_signals (
            run_id TEXT NOT NULL,
            asset TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts TEXT NOT NULL,
            domain TEXT,
            regime TEXT,
            signal_status TEXT,
            confidence REAL,
            quality REAL,
            instability_score REAL,
            reason TEXT,
            data_adequacy TEXT,
            source_type TEXT,
            source_name TEXT,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (run_id, asset, timeframe, ts)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_runs (
            run_id TEXT PRIMARY KEY,
            publishable INTEGER NOT NULL,
            risk_structural REAL,
            confidence REAL,
            risk_level TEXT,
            model_b_mode TEXT,
            model_b_regime TEXT,
            model_c_mode TEXT,
            model_c_regime TEXT,
            publish_blockers_json TEXT NOT NULL,
            shadow_summary_path TEXT NOT NULL,
            raw_json TEXT NOT NULL,
            indexed_at_utc TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_signals_run ON asset_signals(run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_signals_status ON asset_signals(signal_status)")


def _upsert_run(conn: sqlite3.Connection, *, run_id: str, summary: dict[str, Any], summary_path: Path, snapshot_path: Path) -> None:
    gate = summary.get("deployment_gate") if isinstance(summary, dict) else {}
    if not isinstance(gate, dict):
        gate = {}
    reasons = gate.get("reasons") if isinstance(gate.get("reasons"), list) else []
    conn.execute(
        """
        INSERT INTO runs (
            run_id, status, gate_blocked, gate_reasons_json,
            n_assets, validated_signals, watch_signals, inconclusive_signals, validated_ratio,
            policy_path, official_window, summary_path, snapshot_path, indexed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            status=excluded.status,
            gate_blocked=excluded.gate_blocked,
            gate_reasons_json=excluded.gate_reasons_json,
            n_assets=excluded.n_assets,
            validated_signals=excluded.validated_signals,
            watch_signals=excluded.watch_signals,
            inconclusive_signals=excluded.inconclusive_signals,
            validated_ratio=excluded.validated_ratio,
            policy_path=excluded.policy_path,
            official_window=excluded.official_window,
            summary_path=excluded.summary_path,
            snapshot_path=excluded.snapshot_path,
            indexed_at_utc=excluded.indexed_at_utc
        """,
        (
            run_id,
            _to_text(summary.get("status"), "unknown"),
            1 if bool(gate.get("blocked", False)) else 0,
            json.dumps([str(x) for x in reasons], ensure_ascii=False),
            int(_to_float(summary.get("n_assets"), 0.0) or 0),
            int(_to_float(summary.get("validated_signals"), 0.0) or 0),
            int(_to_float(summary.get("watch_signals"), 0.0) or 0),
            int(_to_float(summary.get("inconclusive_signals"), 0.0) or 0),
            float(_to_float(summary.get("validated_ratio"), 0.0) or 0.0),
            _to_text(summary.get("policy_path"), ""),
            _to_float(summary.get("official_window"), None),
            str(summary_path),
            str(snapshot_path),
            _iso_now(),
        ),
    )


def _replace_asset_signals(conn: sqlite3.Connection, *, run_id: str, rows: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM asset_signals WHERE run_id = ?", (run_id,))
    insert_rows = []
    for row in rows:
        insert_rows.append(
            (
                run_id,
                _to_text(row.get("asset"), ""),
                _to_text(row.get("timeframe"), "daily"),
                _to_text(row.get("timestamp"), ""),
                _to_text(row.get("domain"), ""),
                _to_text(row.get("regime"), ""),
                _to_text(row.get("signal_status") or row.get("status"), "inconclusive"),
                _to_float(row.get("confidence"), None),
                _to_float(row.get("quality"), None),
                _to_float(row.get("instability_score"), None),
                _to_text(row.get("reason"), ""),
                _to_text(row.get("data_adequacy"), ""),
                _to_text(row.get("source_type"), ""),
                _to_text(row.get("source_name"), ""),
                json.dumps(row, ensure_ascii=False),
            )
        )
    conn.executemany(
        """
        INSERT INTO asset_signals (
            run_id, asset, timeframe, ts, domain, regime, signal_status, confidence, quality,
            instability_score, reason, data_adequacy, source_type, source_name, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        insert_rows,
    )


def _upsert_copilot(conn: sqlite3.Connection, *, run_id: str, shadow: dict[str, Any], shadow_path: Path) -> None:
    fusion = shadow.get("fusion") if isinstance(shadow, dict) else {}
    if not isinstance(fusion, dict):
        fusion = {}
    model_b = shadow.get("model_b") if isinstance(shadow, dict) else {}
    if not isinstance(model_b, dict):
        model_b = {}
    model_c = shadow.get("model_c") if isinstance(shadow, dict) else {}
    if not isinstance(model_c, dict):
        model_c = {}
    blockers = fusion.get("publish_blockers") if isinstance(fusion.get("publish_blockers"), list) else []
    conn.execute(
        """
        INSERT INTO copilot_runs (
            run_id, publishable, risk_structural, confidence, risk_level,
            model_b_mode, model_b_regime, model_c_mode, model_c_regime,
            publish_blockers_json, shadow_summary_path, raw_json, indexed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            publishable=excluded.publishable,
            risk_structural=excluded.risk_structural,
            confidence=excluded.confidence,
            risk_level=excluded.risk_level,
            model_b_mode=excluded.model_b_mode,
            model_b_regime=excluded.model_b_regime,
            model_c_mode=excluded.model_c_mode,
            model_c_regime=excluded.model_c_regime,
            publish_blockers_json=excluded.publish_blockers_json,
            shadow_summary_path=excluded.shadow_summary_path,
            raw_json=excluded.raw_json,
            indexed_at_utc=excluded.indexed_at_utc
        """,
        (
            run_id,
            1 if bool(fusion.get("publishable", False)) else 0,
            _to_float(fusion.get("risk_structural"), None),
            _to_float(fusion.get("confidence"), None),
            _to_text(fusion.get("risk_level"), ""),
            _to_text(model_b.get("mode"), ""),
            _to_text(model_b.get("predicted_regime"), ""),
            _to_text(model_c.get("mode"), ""),
            _to_text(model_c.get("regime"), ""),
            json.dumps([str(x) for x in blockers], ensure_ascii=False),
            str(shadow_path),
            json.dumps(shadow, ensure_ascii=False),
            _iso_now(),
        ),
    )


def _build_latest_snapshot(conn: sqlite3.Connection, *, run_id: str, db_path: Path) -> dict[str, Any]:
    run_row = conn.execute(
        """
        SELECT run_id, status, gate_blocked, n_assets, validated_signals, watch_signals, inconclusive_signals, validated_ratio
        FROM runs WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    if not run_row:
        return {
            "status": "missing",
            "run_id": run_id,
            "db_path": str(db_path),
            "generated_at_utc": _iso_now(),
        }

    counts = conn.execute("SELECT COUNT(*) FROM asset_signals WHERE run_id = ?", (run_id,)).fetchone()
    domain_rows = conn.execute(
        "SELECT domain, COUNT(*) FROM asset_signals WHERE run_id = ? GROUP BY domain ORDER BY COUNT(*) DESC",
        (run_id,),
    ).fetchall()
    status_rows = conn.execute(
        "SELECT signal_status, COUNT(*) FROM asset_signals WHERE run_id = ? GROUP BY signal_status ORDER BY COUNT(*) DESC",
        (run_id,),
    ).fetchall()
    cp_row = conn.execute(
        "SELECT publishable, risk_structural, confidence, risk_level FROM copilot_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    total_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()
    total_assets = conn.execute("SELECT COUNT(*) FROM asset_signals").fetchone()

    return {
        "status": "ok",
        "run_id": run_id,
        "generated_at_utc": _iso_now(),
        "db_path": str(db_path),
        "counts": {
            "runs_total": int((total_runs[0] if total_runs else 0) or 0),
            "asset_rows_total": int((total_assets[0] if total_assets else 0) or 0),
            "asset_rows_for_run": int((counts[0] if counts else 0) or 0),
        },
        "run": {
            "status": str(run_row[1]),
            "gate_blocked": bool(run_row[2]),
            "n_assets": int(run_row[3]),
            "validated_signals": int(run_row[4]),
            "watch_signals": int(run_row[5]),
            "inconclusive_signals": int(run_row[6]),
            "validated_ratio": float(run_row[7]),
        },
        "domains": [{"domain": str(r[0]), "count": int(r[1])} for r in domain_rows],
        "signal_status": [{"status": str(r[0]), "count": int(r[1])} for r in status_rows],
        "copilot": {
            "row_exists": cp_row is not None,
            "publishable": bool(cp_row[0]) if cp_row else False,
            "risk_structural": float(cp_row[1]) if cp_row and cp_row[1] is not None else None,
            "confidence": float(cp_row[2]) if cp_row and cp_row[2] is not None else None,
            "risk_level": str(cp_row[3]) if cp_row and cp_row[3] is not None else "indefinido",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest run artifacts into platform SQLite database.")
    parser.add_argument("--run-id", type=str, default="", help="Run id em results/ops/snapshots.")
    parser.add_argument("--db-path", type=str, default="results/platform/assyntrax_platform.db")
    parser.add_argument("--snapshot-root", type=str, default="results/ops/snapshots")
    parser.add_argument("--copilot-root", type=str, default="results/ops/copilot")
    parser.add_argument("--out-json", type=str, default="results/platform/latest_db_snapshot.json")
    parser.add_argument("--latest-release", type=str, default="results/platform/latest_release.json")
    args = parser.parse_args()

    run_id = _resolve_run_id(args.run_id.strip() or None)
    snapshot_dir = ROOT / args.snapshot_root / run_id
    summary_path = snapshot_dir / "summary.json"
    api_snapshot_path = snapshot_dir / "api_snapshot.jsonl"
    if not summary_path.exists() or not api_snapshot_path.exists():
        raise FileNotFoundError(f"snapshot incompleto para run {run_id}: {snapshot_dir}")

    summary = _read_json(summary_path, {})
    rows = _read_jsonl(api_snapshot_path)

    copilot_shadow_path = ROOT / args.copilot_root / run_id / "shadow_summary.json"
    copilot_shadow = _read_json(copilot_shadow_path, {})

    db_path = ROOT / args.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        _init_db(conn)
        _upsert_run(
            conn,
            run_id=run_id,
            summary=summary if isinstance(summary, dict) else {},
            summary_path=summary_path,
            snapshot_path=api_snapshot_path,
        )
        _replace_asset_signals(conn, run_id=run_id, rows=rows)
        if isinstance(copilot_shadow, dict) and copilot_shadow:
            _upsert_copilot(conn, run_id=run_id, shadow=copilot_shadow, shadow_path=copilot_shadow_path)
        conn.commit()

        latest_payload = _build_latest_snapshot(conn, run_id=run_id, db_path=db_path)
    finally:
        conn.close()

    out_json = ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(latest_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    latest_release = {
        "updated_at_utc": _iso_now(),
        "run_id": run_id,
        "db_path": str(db_path),
        "latest_db_snapshot": str(out_json),
    }
    latest_release_path = ROOT / args.latest_release
    latest_release_path.parent.mkdir(parents=True, exist_ok=True)
    latest_release_path.write_text(json.dumps(latest_release, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[platform_db] run_id={run_id} rows={len(rows)} "
        f"copilot_row={'yes' if bool(latest_payload.get('copilot', {}).get('row_exists', False)) else 'no'}"
    )


if __name__ == "__main__":
    main()
