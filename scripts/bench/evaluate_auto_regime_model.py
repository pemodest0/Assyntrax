"""Avalia o modelo automatico de regimes com metrics e matriz de confusao."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.diagnostics.auto_regime_model import (
    build_training_dataset,
    build_training_dataset_with_meta,
    load_auto_regime_model,
    train_auto_regime_model,
)


def _safe_import_sklearn():
    try:
        from sklearn.metrics import classification_report, confusion_matrix
        from sklearn.model_selection import train_test_split
        return classification_report, confusion_matrix, train_test_split
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("scikit-learn Ã© necessÃ¡rio para avaliaÃ§Ã£o.") from exc


def write_confusion_csv(path: Path, labels: list[str], matrix: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as handle:
        header = ",".join(["label"] + labels)
        handle.write(header + "\n")
        for label, row in zip(labels, matrix):
            handle.write(",".join([label] + [str(int(v)) for v in row]) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o modelo automatico de regimes.")
    parser.add_argument("--results", type=str, default="results", help="Pasta com summary*.csv.")
    parser.add_argument("--model-dir", type=str, default="models", help="Pasta do modelo treinado.")
    parser.add_argument("--outdir", type=str, default="results/auto_regime_eval")
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--kfold", type=int, default=5)
    parser.add_argument("--group-kfold", action="store_true", help="K-fold por sÃ©rie (GroupKFold).")
    parser.add_argument("--group-holdout", action="store_true", help="Holdout por sÃ©rie (GroupShuffleSplit).")
    args = parser.parse_args()

    results_root = Path(args.results)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.group_kfold or args.group_holdout:
        X, y, groups = build_training_dataset_with_meta(results_root)
    else:
        X, y = build_training_dataset(results_root)
        groups = None
    if args.min_count > 1:
        unique, counts = np.unique(y, return_counts=True)
        keep_labels = {label for label, count in zip(unique, counts) if count >= args.min_count}
        keep_mask = np.array([label in keep_labels for label in y])
        X = X[keep_mask]
        y = y[keep_mask]
        if groups is not None:
            groups = [g for g, keep in zip(groups, keep_mask) if keep]
    unique_labels = sorted({str(label) for label in y})

    classification_report, confusion_matrix, train_test_split = _safe_import_sklearn()

    model_path = Path(args.model_dir) / "auto_regime_model.joblib"
    meta_path = Path(args.model_dir) / "auto_regime_model_meta.json"
    if model_path.exists():
        auto_model = load_auto_regime_model(model_path, meta_path)
    else:
        auto_model = train_auto_regime_model(results_root, model_path, meta_path)

    # In-sample evaluation
    preds = auto_model.model.predict(X)
    report_in = classification_report(y, preds, labels=unique_labels, output_dict=True, zero_division=0)
    conf_in = confusion_matrix(y, preds, labels=unique_labels)

    # Holdout evaluation
    unique, counts = np.unique(y, return_counts=True)
    min_count = int(counts.min()) if counts.size else 0
    stratify = y if min_count >= 2 else None
    if args.group_holdout and groups is not None:
        from sklearn.model_selection import GroupShuffleSplit

        splitter = GroupShuffleSplit(test_size=args.test_size, n_splits=1, random_state=42)
        train_idx, test_idx = next(splitter.split(X, y, groups))
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42, stratify=stratify
        )
    fresh_model = train_auto_regime_model(
        results_root,
        model_path=out_dir / "temp_model.joblib",
        meta_path=out_dir / "temp_model_meta.json",
    ).model
    fresh_model.fit(X_train, y_train)
    preds_test = fresh_model.predict(X_test)
    report_holdout = classification_report(
        y_test, preds_test, labels=unique_labels, output_dict=True, zero_division=0
    )
    conf_holdout = confusion_matrix(y_test, preds_test, labels=unique_labels)

    # Cross-validation (quando possÃ­vel)
    cv_scores: dict[str, float] | None = None
    if args.kfold >= 2 and min_count >= args.kfold:
        from sklearn.metrics import f1_score
        if args.group_kfold and groups is not None:
            from sklearn.model_selection import GroupKFold

            gkf = GroupKFold(n_splits=args.kfold)
            splits = gkf.split(X, y, groups)
        else:
            from sklearn.model_selection import StratifiedKFold

            skf = StratifiedKFold(n_splits=args.kfold, shuffle=True, random_state=42)
            splits = skf.split(X, y)

        scores = []
        for train_idx, test_idx in splits:
            model_cv = train_auto_regime_model(
                results_root,
                model_path=out_dir / "temp_model.joblib",
                meta_path=out_dir / "temp_model_meta.json",
            ).model
            model_cv.fit(X[train_idx], y[train_idx])
            preds_cv = model_cv.predict(X[test_idx])
            scores.append(f1_score(y[test_idx], preds_cv, average="weighted", zero_division=0))
        cv_scores = {
            "weighted_f1_mean": float(np.mean(scores)),
            "weighted_f1_std": float(np.std(scores)),
            "folds": args.kfold,
            "group_kfold": bool(args.group_kfold),
        }

    (out_dir / "classification_report_in_sample.json").write_text(
        json.dumps(report_in, indent=2), encoding="utf-8"
    )
    (out_dir / "classification_report_holdout.json").write_text(
        json.dumps(report_holdout, indent=2), encoding="utf-8"
    )
    if cv_scores is not None:
        (out_dir / "cv_scores.json").write_text(
            json.dumps(cv_scores, indent=2), encoding="utf-8"
        )
    write_confusion_csv(out_dir / "confusion_in_sample.csv", unique_labels, conf_in)
    write_confusion_csv(out_dir / "confusion_holdout.csv", unique_labels, conf_holdout)

    md_lines = [
        "# Avaliacao do modelo automatico",
        "",
        f"- Min count usado: {args.min_count}",
        f"- K-fold: {args.kfold}",
        f"- Group K-fold: {args.group_kfold}",
        f"- Group holdout: {args.group_holdout}",
        "",
        "## In-sample",
        "```json",
        json.dumps(report_in, indent=2),
        "```",
        "",
        "## Holdout",
        "```json",
        json.dumps(report_holdout, indent=2),
        "```",
        "",
    ]
    if cv_scores is not None:
        md_lines.extend(
            [
                "## Cross-validation",
                "```json",
                json.dumps(cv_scores, indent=2),
                "```",
                "",
            ]
        )
    (out_dir / "report.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Relatorios salvos em: {out_dir}")


if __name__ == "__main__":
    main()

