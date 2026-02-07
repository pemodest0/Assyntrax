#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _load_forecast_rows(root: Path) -> List[Tuple[str, str, str, str, Dict]]:
    rows = []
    for f in root.rglob("*_log_return_h*.json"):
        asset = f.parents[1].name if len(f.parents) >= 2 else ""
        tf = f.parents[0].name if len(f.parents) >= 1 else ""
        horizon = f.name.split("_h")[-1].replace(".json", "")
        data = json.loads(f.read_text())
        by_year = data.get("by_year", {})
        if not by_year:
            continue
        for year, yd in by_year.items():
            overall = yd.get("overall", {})
            auto = overall.get("auto_best")
            if auto:
                rows.append((asset, tf, horizon, str(year), auto))
    return rows


def _summarize_forecast(rows: List[Tuple[str, str, str, str, Dict]]) -> Dict:
    if not rows:
        return {"note": "no forecast rows found"}
    df = pd.DataFrame(
        [(a, tf, h, y, d.get("mase"), d.get("dir_acc")) for a, tf, h, y, d in rows],
        columns=["asset", "tf", "horizon", "year", "mase", "dir_acc"],
    )
    df = df.dropna(subset=["mase"])
    summary = {
        "count": int(len(df)),
        "mase_min": float(df["mase"].min()),
        "mase_median": float(df["mase"].median()),
        "mase_p90": float(df["mase"].quantile(0.9)),
        "dir_acc_median": float(df["dir_acc"].median()) if df["dir_acc"].notna().any() else None,
    }
    # top performers (lowest MASE)
    best = df.sort_values("mase").head(10).to_dict(orient="records")
    summary["best_examples"] = best
    return summary


def _load_compare_summary(path: Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _summarize_turning_points(compare: Dict) -> Dict:
    out = {}
    for key, val in compare.items():
        tp = val.get("turning_points", {})
        out[key] = {
            "macro": tp.get("macro"),
            "stress": tp.get("stress"),
            "vol": tp.get("vol"),
        }
    return out


def _load_audit(path: Path) -> Dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("counts", {})


def build_report(forecast: Dict, turning: Dict, audit: Dict) -> str:
    lines = []
    lines.append("# Superteste Assyntrax (Resumo Executivo)")
    lines.append("")
    lines.append("## Forecast condicional (auto_best)")
    if "note" in forecast:
        lines.append(f"- {forecast['note']}")
    else:
        lines.append(f"- Total de janelas avaliadas: **{forecast['count']}**")
        lines.append(f"- MASE (mediana): **{forecast['mase_median']:.3f}**")
        lines.append(f"- MASE (p90): **{forecast['mase_p90']:.3f}**")
        lines.append(f"- MASE (mín): **{forecast['mase_min']:.3f}**")
        if forecast.get("dir_acc_median") is not None:
            lines.append(f"- Direção (mediana): **{forecast['dir_acc_median']:.3f}**")
        lines.append("")
        lines.append("**Exemplos de melhor desempenho (menor MASE):**")
        for row in forecast.get("best_examples", [])[:6]:
            lines.append(
                f"- {row['asset']} {row['tf']} h{row['horizon']} ({row['year']}): MASE {row['mase']:.3f}"
            )
    lines.append("")
    lines.append("## Regimes vs proxies (turning points)")
    if not turning:
        lines.append("- Sem compare_summary disponível.")
    else:
        for key, val in turning.items():
            lines.append(f"- **{key}**")
            for name in ("macro", "stress", "vol"):
                met = val.get(name) or {}
                if met:
                    lines.append(
                        f"  - {name}: hit_rate {met.get('hit_rate', 0):.3f}, false_alarm_rate {met.get('false_alarm_rate', 0):.3f}"
                    )
    lines.append("")
    lines.append("## Saúde do motor (última execução)")
    if not audit:
        lines.append("- Sem audit disponível.")
    else:
        lines.append(f"- Total ativos: **{audit.get('total')}**")
        lines.append(f"- Changed: **{audit.get('changed')}**")
        lines.append(f"- LOW_CONF: **{audit.get('low_conf')}**")
        lines.append(f"- UNSTABLE: **{audit.get('unstable')}**")
        lines.append(f"- Reliable: **{audit.get('reliable')}**")
    lines.append("")
    lines.append("## Narrativa de venda (honesta)")
    lines.append(
        "- O motor entrega **forecast sempre** e **grau de confiança** por regime. "
        "Isso permite operar quando há estrutura e reduzir exposição em transição."
    )
    lines.append(
        "- Em regimes estáveis, o desempenho melhora; em regimes de transição, o motor "
        "prioriza alerta e transparência (evita falsas certezas)."
    )
    lines.append(
        "- O produto vende **disciplina de risco**, não promessa de acerto absoluto."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sales supertest report.")
    parser.add_argument("--forecast-dir", default="results/forecast_suite")
    parser.add_argument("--compare-summary", default="results/official_regimes/compare/compare_summary.json")
    parser.add_argument("--audit-daily", default="results/latest_graph/audit_daily.json")
    parser.add_argument("--outdir", default="results/sales_supertest")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    forecast_rows = _load_forecast_rows(Path(args.forecast_dir))
    forecast_summary = _summarize_forecast(forecast_rows)
    turning = _summarize_turning_points(_load_compare_summary(Path(args.compare_summary)))
    audit = _load_audit(Path(args.audit_daily))

    report = build_report(forecast_summary, turning, audit)
    report_path = outdir / "supertest_report.md"
    report_path.write_text(report, encoding="utf-8")
    (outdir / "supertest_report.json").write_text(
        json.dumps(
            {
                "forecast": forecast_summary,
                "turning_points": turning,
                "audit": audit,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[ok] wrote {report_path}")


if __name__ == "__main__":
    main()
