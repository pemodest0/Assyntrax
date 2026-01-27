"""Extrai o PDF de contexto e gera um Markdown organizado por ativo."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MONTHS = r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)"
DASH = r"[-–]"
DATE_RANGE = rf"(?P<data1>\d{{1,2}}\s*(?:{DASH}\s*\d{{1,2}})?\s+{MONTHS}\s+\d{{4}})"
DATE_RANGE_2 = rf"(?P<data2>\d{{1,2}}\s+{MONTHS}\s+\d{{4}}\s*{DASH}\s*\d{{1,2}}\s+{MONTHS}\s+\d{{4}})"
PCT = r"(?P<variacao>[+-–]?\d+(?:,\d+)?%)"

MOJIBAKE_MAP = {
    "Ã¡": "á",
    "Ã¢": "â",
    "Ã£": "ã",
    "Ã¤": "ä",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã­": "í",
    "Ã³": "ó",
    "Ã´": "ô",
    "Ãµ": "õ",
    "Ã¶": "ö",
    "Ãº": "ú",
    "Ã¼": "ü",
    "Ã§": "ç",
    "Ã“": "Ó",
    "Ã‰": "É",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã“": "Ó",
    "Ã": "Á",
    "Ã‚": "Â",
    "Ãƒ": "Ã",
    "Ã‰": "É",
    "Ã": "Í",
    "Ã“": "Ó",
    "Ãš": "Ú",
    "Ã‡": "Ç",
    "â€“": "–",
    "â€”": "—",
    "â€œ": "“",
    "â€": "”",
    "â€˜": "‘",
    "â€™": "’",
    "â€¦": "…",
}


def extract_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Instale pypdf: python -m pip install pypdf"
        ) from exc

    reader = PdfReader(str(pdf_path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text


def normalize(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2013", "–")
    # join broken date ranges like "29 mar –\n4 abr 2025"
    text = re.sub(
        rf"(\d{{1,2}}\s+{MONTHS})\s*{DASH}\s*\n\s*(\d{{1,2}}\s+{MONTHS}\s+\d{{4}})",
        r"\1 – \2",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    # Remove bullet artifacts like "• 1 2 3"
    text = re.sub(r"(?:\s*•\s*\d+)+", " ", text)
    text = text.replace("•", " ")
    # Remove footnote-like stray numbers between sentences
    text = re.sub(r"\s\d+(?:\s\d+)+\s", " ", text)
    return text.strip()


def fix_mojibake(text: str) -> str:
    # Try latin1->utf8 first
    try:
        fixed = text.encode("latin1").decode("utf-8")
        if fixed != text:
            text = fixed
    except Exception:
        pass
    for bad, good in MOJIBAKE_MAP.items():
        text = text.replace(bad, good)
    return text


def heading_variants(heading: str) -> list[str]:
    variants = [heading]
    try:
        mojibake = heading.encode("utf-8").decode("latin1")
        if mojibake != heading:
            variants.append(mojibake)
    except Exception:
        pass
    return variants


def split_sections(text: str) -> list[tuple[str, str]]:
    headings = [
        "VIX (Índice de Volatilidade)",
        "SPY (ETF S&P 500)",
        "GSPC (Índice S&P 500)",
        "DX-Y.NYB (Índice Dólar – Dollar Index)",
        "DGS10 (Juros do Tesouro Americano 10 anos)",
        "DGS2 (Juros do Tesouro Americano 2 anos)",
    ]
    indexes = []
    for head in headings:
        for variant in heading_variants(head):
            idx = text.find(variant)
            if idx >= 0:
                indexes.append((idx, head))
                break
    if not indexes:
        return [("Documento", text)]
    indexes.sort()
    sections = []
    for i, (start, head) in enumerate(indexes):
        end = indexes[i + 1][0] if i + 1 < len(indexes) else len(text)
        sections.append((head, text[start:end].strip()))
    return sections


def clean_desc(desc: str) -> str:
    # Remove dangling date fragments like "29 mar –"
    desc = re.sub(rf"\b\d{{1,2}}\s+{MONTHS}\s+{DASH}\s*$", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"\s{2,}", " ", desc)
    return desc.strip()


def extract_events(section_text: str) -> list[dict[str, str]]:
    events = []
    pattern = re.compile(rf"(?:{DATE_RANGE_2}|{DATE_RANGE})\s*\(\s*{PCT}\s*\)\s*:\s*")
    matches = list(pattern.finditer(section_text))
    if not matches:
        return events
    for i, match in enumerate(matches):
        date = match.group("data2") or match.group("data1")
        pct = match.group("variacao")
        if not date or not pct:
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        desc = section_text[start:end].strip()
        desc = re.sub(r"\s+", " ", desc)
        desc = clean_desc(desc)
        events.append({"data": date, "variacao": pct, "descricao": desc})
    return events


def build_markdown(sections: list[tuple[str, str]]) -> str:
    lines = [
        "# Contexto de Eventos (PDF extraído)",
        "",
        "Este arquivo organiza os eventos por ativo com datas e variações.",
        "",
    ]
    for title, content in sections:
        lines.append(f"## {title}")
        events = extract_events(content)
        if events:
            lines.append("| Data | Variação | Descrição |")
            lines.append("| --- | --- | --- |")
            for ev in events:
                lines.append(f"| {ev['data']} | {ev['variacao']} | {ev['descricao']} |")
        else:
            lines.append(content)
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai PDF e gera Markdown.")
    parser.add_argument("--pdf", default="VIX (Índice de Volatilidade).pdf")
    parser.add_argument("--out", default="results/vix_context.md")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF não encontrado: {pdf_path}")

    text = extract_text(pdf_path)
    text = fix_mojibake(text)
    text = normalize(text)
    text = fix_mojibake(text)
    sections = split_sections(text)
    md = build_markdown(sections)
    md = fix_mojibake(md)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
