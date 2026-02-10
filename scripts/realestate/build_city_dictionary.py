#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REGION_BY_STATE = {
    "BR": "Brasil",
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}

CITY_TO_STATE = {
    "indice fipezap": "BR",
    "aracaju": "SE",
    "balneario camboriu": "SC",
    "barueri": "SP",
    "sao paulo": "SP",
    "rio de janeiro": "RJ",
    "belo horizonte": "MG",
    "brasilia": "DF",
    "porto alegre": "RS",
    "curitiba": "PR",
    "florianopolis": "SC",
    "salvador": "BA",
    "recife": "PE",
    "fortaleza": "CE",
    "goiania": "GO",
    "campo grande": "MS",
    "cuiaba": "MT",
    "manaus": "AM",
    "belem": "PA",
    "vitoria": "ES",
    "betim": "MG",
    "blumenau": "SC",
    "campinas": "SP",
    "canoas": "RS",
    "caxias do sul": "RS",
    "contagem": "MG",
    "diadema": "SP",
    "guaruja": "SP",
    "guarulhos": "SP",
    "itajai": "SC",
    "itapema": "SC",
    "jaboatao dos guararapes": "PE",
    "joinville": "SC",
    "joao pessoa": "PB",
    "londrina": "PR",
    "maceio": "AL",
    "natal": "RN",
    "niteroi": "RJ",
    "novo hamburgo": "RS",
    "osasco": "SP",
    "pelotas": "RS",
    "praia grande": "SP",
    "ribeirao preto": "SP",
    "santa maria": "RS",
    "santos": "SP",
    "santo andre": "SP",
    "sao bernardo do campo": "SP",
    "sao caetano do sul": "SP",
    "sao jose dos campos": "SP",
    "sao jose dos pinhais": "PR",
    "sao jose do rio preto": "SP",
    "sao jose": "SC",
    "sao leopoldo": "RS",
    "sao luis": "MA",
    "sao vicente": "SP",
    "teresina": "PI",
    "vila velha": "ES",
}


def normalize_text(s: str) -> str:
    import unicodedata

    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build versioned city/UF/region dictionary for real-estate assets.")
    parser.add_argument("--core-dir", type=str, default="data/realestate/core")
    parser.add_argument("--out", type=str, default="config/realestate_city_uf_region.v1.json")
    args = parser.parse_args()

    core_dir = ROOT / args.core_dir
    rows = []
    for p in sorted(core_dir.glob("*_core.csv")):
        stem = p.stem
        city = stem.replace("FipeZap_", "").replace("_Total_core", "").replace("_", " ")
        nk = normalize_text(city)
        uf = CITY_TO_STATE.get(nk, "NA")
        region = REGION_BY_STATE.get(uf, "Desconhecida")
        rows.append(
            {
                "asset": stem.replace("_core", ""),
                "city": city,
                "city_key": nk,
                "uf": uf,
                "region": region,
                "source_type": "official",
                "source_name": "fipezap_core",
            }
        )

    payload = {
        "version": "v1.0.0",
        "generated_from": str(core_dir),
        "total_assets": len(rows),
        "entries": rows,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[city_dict] ok assets={len(rows)} out={out}")


if __name__ == "__main__":
    main()
