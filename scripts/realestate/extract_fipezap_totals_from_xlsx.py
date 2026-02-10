#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def _normalize_asset_name(raw: str) -> str:
    safe = re.sub(r"\s+", "_", raw.strip())
    safe = re.sub(r"[^0-9A-Za-z_\-À-ÿ]", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe


def _col_to_idx(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _excel_serial_to_date(value: float) -> dt.date:
    base = dt.datetime(1899, 12, 30)
    return (base + dt.timedelta(days=float(value))).date()


def _parse_shared_strings(z: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out: list[str] = []
    for si in root.findall(f".//{{{NS_MAIN}}}si"):
        parts = [t.text or "" for t in si.findall(f".//{{{NS_MAIN}}}t")]
        out.append("".join(parts))
    return out


def _sheet_targets(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map: dict[str, str] = {}
    for rel in rels.findall(f".//{{{NS_PKG_REL}}}Relationship"):
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rid and target:
            rel_map[rid] = target

    out: list[tuple[str, str]] = []
    for sheet in wb.findall(f".//{{{NS_MAIN}}}sheet"):
        name = sheet.attrib.get("name", "")
        rid = sheet.attrib.get(f"{{{NS_REL}}}id")
        if not rid:
            continue
        target = rel_map.get(rid)
        if not target:
            continue
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        out.append((name, target))
    return out


def _read_cell_value(c: ET.Element, shared: list[str]) -> str:
    t = c.attrib.get("t")
    if t == "inlineStr":
        node = c.find(f".//{{{NS_MAIN}}}t")
        return (node.text or "").strip() if node is not None else ""
    v = c.find(f"{{{NS_MAIN}}}v")
    if v is None or v.text is None:
        return ""
    raw = v.text.strip()
    if t == "s":
        try:
            return shared[int(raw)].strip()
        except Exception:
            return ""
    return raw


def _extract_sheet_rows(z: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[dict[str, str]]:
    root = ET.fromstring(z.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.findall(f".//{{{NS_MAIN}}}row"):
        cells = row.findall(f"{{{NS_MAIN}}}c")
        if not cells:
            continue
        max_idx = 0
        parsed: dict[int, str] = {}
        for c in cells:
            ref = c.attrib.get("r", "")
            if not ref:
                continue
            idx = _col_to_idx(ref)
            parsed[idx] = _read_cell_value(c, shared)
            max_idx = max(max_idx, idx)
        arr = [""] * (max_idx + 1)
        for idx, val in parsed.items():
            arr[idx] = val
        rows.append(arr)

    header_idx = -1
    date_col = -1
    total_col = -1
    for i, row in enumerate(rows[:20]):
        up = [c.strip().upper() for c in row]
        if "DATA" in up and "TOTAL" in up:
            header_idx = i
            date_col = up.index("DATA")
            total_col = up.index("TOTAL")
            break
    if header_idx < 0:
        return []

    out: list[dict[str, str]] = []
    for row in rows[header_idx + 1 :]:
        if date_col >= len(row) or total_col >= len(row):
            continue
        d = row[date_col].strip()
        v = row[total_col].strip().replace(",", ".")
        if not d or not v:
            continue
        parsed_date = None
        if re.fullmatch(r"\d+(\.\d+)?", d):
            try:
                parsed_date = _excel_serial_to_date(float(d))
            except Exception:
                parsed_date = None
        else:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%Y"):
                try:
                    dt_val = dt.datetime.strptime(d, fmt)
                    if fmt == "%m/%Y":
                        dt_val = dt_val.replace(day=1)
                    parsed_date = dt_val.date()
                    break
                except Exception:
                    continue
        if parsed_date is None:
            continue
        try:
            val = float(v)
        except Exception:
            continue
        out.append({"date": parsed_date.isoformat(), "value": f"{val:.8f}"})
    return out


def extract_workbook(xlsx_path: Path, outdir: Path) -> list[Path]:
    produced: list[Path] = []
    outdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(xlsx_path, "r") as z:
        shared = _parse_shared_strings(z)
        for sheet_name, target in _sheet_targets(z):
            try:
                rows = _extract_sheet_rows(z, target, shared)
            except Exception:
                continue
            if len(rows) < 24:
                continue
            asset = _normalize_asset_name(sheet_name)
            dest = outdir / f"FipeZap_{asset}_Total.csv"
            with dest.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["date", "value"])
                writer.writeheader()
                writer.writerows(rows)
            produced.append(dest)
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai series FipeZap Total dos xlsx locais sem dependencias externas.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/raw/realestate/fipezap/fipezap_serieshistoricas.xlsx",
            "data/raw/realestate/fipezap/fipezap_historico.xlsx",
        ],
    )
    parser.add_argument("--outdir", default="data/realestate/normalized")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    total = 0
    for item in args.inputs:
        path = Path(item)
        if not path.exists():
            print(f"[skip] missing {path}")
            continue
        produced = extract_workbook(path, outdir)
        print(f"[ok] {path.name}: {len(produced)} series extraidas")
        total += len(produced)
    print(f"[done] total series extraidas: {total}")


if __name__ == "__main__":
    main()

