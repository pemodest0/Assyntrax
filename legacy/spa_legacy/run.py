from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from spa.adapters.ons import normalize_ons
from spa.diagnostics import run_diagnostics
from spa.forecast import forecast_series
from spa.features import compute_features
from spa.io import load_dataset
from spa.preprocess import preprocess
from spa.report import generate_report


def _format_percent(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}{abs(value):.1f}%"


def _comparacao_texto(valor: float, media: float, janela: int) -> str:
    if media == 0:
        return f"Sem comparação para {janela} pontos (média zero)."
    delta_pct = (valor - media) / media * 100
    sentido = "acima" if delta_pct >= 0 else "abaixo"
    return (
        f"O último ponto está {_format_percent(delta_pct)} {sentido} "
        f"da média dos últimos {janela} pontos."
    )


def _mudanca_2_semanas(values: list[float], limiar: float = 0.05) -> tuple[Optional[bool], Optional[float]]:
    if len(values) < 28:
        return None, None
    ultimos = values[-14:]
    anteriores = values[-28:-14]
    media_ult = float(sum(ultimos) / len(ultimos))
    media_ant = float(sum(anteriores) / len(anteriores))
    if media_ant == 0:
        return None, None
    delta_pct = (media_ult - media_ant) / media_ant
    mudou = abs(delta_pct) >= limiar
    return mudou, float(delta_pct * 100)


def _detectar_regioes(df: pd.DataFrame) -> tuple[list[str], Optional[str]]:
    for col in ["nom_subsistema", "id_subsistema", "subsistema"]:
        if col in df.columns:
            valores = [str(v) for v in df[col].dropna().unique().tolist()]
            return sorted(set(valores)), col
    return [], None


def _infer_region_key(name: str) -> str:
    lower = name.lower()
    if "norte" in lower:
        return "N"
    if "nordeste" in lower:
        return "NE"
    if "sudeste" in lower or "centro-oeste" in lower:
        return "SE/CO"
    if "sul" in lower:
        return "S"
    return name


def _descricao_dado_ons(ons_mode: str, regiao_analisada: str, passo_de_tempo: str) -> str:
    base = (
        "Este relatório analisa a demanda média diária de energia elétrica. "
        "A carga elétrica indica quanta energia o sistema precisou atender, "
        "medida em megawatts médios (MWmed). "
    )
    if ons_mode == "sum":
        base += "Os valores das regiões foram somados para representar o sistema como um todo. "
    else:
        base += f"O valor representa apenas a região {regiao_analisada}. "

    if "dia" in passo_de_tempo:
        base += "Pelo espaçamento de tempo, parece ser um dado diário."
    elif "hora" in passo_de_tempo:
        base += "Pelo espaçamento de tempo, parece ser um dado horário."
    else:
        base += f"O passo de tempo estimado foi: {passo_de_tempo}."
    return base


def _passo_texto(dt_seconds: float) -> tuple[str, str]:
    if dt_seconds != dt_seconds:
        return "irregular", "Cada ponto representa um intervalo de tempo irregular."
    if dt_seconds % 86400 == 0:
        dias = int(dt_seconds / 86400)
        return f"{dias} dia(s)", f"Cada ponto representa {dias} dia(s)."
    if dt_seconds % 3600 == 0:
        horas = int(dt_seconds / 3600)
        return f"{horas} hora(s)", f"Cada ponto representa {horas} hora(s)."
    if dt_seconds % 60 == 0:
        minutos = int(dt_seconds / 60)
        return f"{minutos} minuto(s)", f"Cada ponto representa {minutos} minuto(s)."
    return f"{dt_seconds:.0f} segundo(s)", f"Cada ponto representa cerca de {dt_seconds:.0f} segundo(s)."


def _build_summary(
    processed_df: pd.DataFrame,
    value_col: str,
    feats: dict,
    diagnostics: dict,
    meta: dict,
    passo_de_tempo: str,
    passo_texto: str,
    regiao_analisada: str,
    ons_mode: str,
    previsao_curta: str,
    obs_previsao: str,
    previsao_texto: str,
) -> dict:
    valores = processed_df[value_col].tolist()
    valor_ultimo = float(valores[-1])

    media_30 = float(np.mean(valores[-30:])) if len(valores) >= 30 else None
    desvio_30 = float(np.std(valores[-30:], ddof=1)) if len(valores) >= 30 else None
    media_365 = float(np.mean(valores[-365:])) if len(valores) >= 365 else None
    desvio_365 = float(np.std(valores[-365:], ddof=1)) if len(valores) >= 365 else None

    comparacao_30d = (
        _comparacao_texto(valor_ultimo, media_30, 30)
        if media_30 is not None
        else "Sem dados suficientes para 30 pontos."
    )
    comparacao_365d = (
        _comparacao_texto(valor_ultimo, media_365, 365)
        if media_365 is not None
        else "Sem dados suficientes para 365 pontos."
    )

    faixa_normal_30d = None
    fora_do_normal = None
    if media_30 is not None and desvio_30 is not None:
        faixa_normal_30d = [media_30 - 2 * desvio_30, media_30 + 2 * desvio_30]
        fora_do_normal = valor_ultimo < faixa_normal_30d[0] or valor_ultimo > faixa_normal_30d[1]

    mudou_2s, mudou_2s_pct = _mudanca_2_semanas(valores)

    data_inicial = processed_df["time"].iloc[0]
    data_final = processed_df["time"].iloc[-1]
    data_inicial_str = data_inicial.strftime("%d/%m/%Y")
    data_final_str = data_final.strftime("%d/%m/%Y")
    total_de_dias = int(len(processed_df))

    o_que_e_esse_numero_texto = _descricao_dado_ons(ons_mode, regiao_analisada, passo_de_tempo)
    periodo_texto = (
        f"O período analisado vai de {data_inicial_str} até {data_final_str}, "
        f"totalizando {total_de_dias} dias. {passo_texto}"
    )

    observacoes = []
    if fora_do_normal is True:
        observacoes.append("O último valor ficou fora do normal recente.")
    elif fora_do_normal is False:
        observacoes.append("O último valor ficou dentro do normal recente.")
    else:
        observacoes.append("Não foi possível comparar com o normal recente.")

    if mudou_2s is True:
        observacoes.append("Houve mudança nas últimas 2 semanas.")
    elif mudou_2s is False:
        observacoes.append("Não houve mudança forte nas últimas 2 semanas.")
    else:
        observacoes.append("Sem dados suficientes para comparar 2 semanas.")

    if meta["confianca"] == "baixa":
        observacoes.append("Os dados tiveram muitos ajustes ou falhas.")
    observacoes_texto = " ".join(observacoes)

    situacao_atual = (
        f"{comparacao_30d} "
        "Isso mostra se o valor mais recente está dentro do padrão esperado. "
        "Quando o valor foge do normal, vale investigar se houve mudança real "
        "no consumo ou algum problema nos dados."
    )

    if mudou_2s is True:
        mudancas_recentes = (
            f"Houve mudança relevante nas últimas duas semanas ({mudou_2s_pct:.1f}%). "
            "Isso pode sinalizar uma alteração real de comportamento ou um evento pontual."
        )
    elif mudou_2s is False:
        mudancas_recentes = (
            f"Não houve mudança relevante nas últimas duas semanas ({mudou_2s_pct:.1f}%). "
            "Isso sugere estabilidade recente."
        )
    else:
        mudancas_recentes = (
            "Não há dados suficientes para comparar as últimas duas semanas. "
            "Sem essa comparação, o diagnóstico recente fica mais limitado."
        )

    o_que_fazer = [
        "Conferir se a fonte dos dados está completa e sem falhas de registro.",
        "Acompanhar a série nos próximos dias para confirmar se o padrão se mantém.",
        "Se a nota de risco estiver alta, investigar causas locais e eventos recentes.",
    ]

    anormalidade = None
    if media_30 is not None and desvio_30 not in (None, 0):
        anormalidade = abs((valor_ultimo - media_30) / desvio_30)

    return {
        "passo_de_tempo": passo_de_tempo,
        "passo_de_tempo_explicado": passo_texto,
        "data_inicial": data_inicial_str,
        "data_final": data_final_str,
        "total_de_dias": total_de_dias,
        "nivel_de_ruido": float(feats["std"]),
        "mudou_de_comportamento": bool(diagnostics.get("regime_change", {}).get("change_detected")),
        "nota_de_risco": int(diagnostics.get("risk_score", 0)),
        "confianca": meta["confianca"],
        "o_que_e_esse_numero": o_que_e_esse_numero_texto,
        "periodo_analisado": periodo_texto,
        "situacao_atual": situacao_atual,
        "mudancas_recentes": mudancas_recentes,
        "observacoes": observacoes_texto,
        "o_que_fazer": o_que_fazer,
        "valor_ultimo": valor_ultimo,
        "comparacao_30d": comparacao_30d,
        "comparacao_365d": comparacao_365d,
        "faixa_normal_30d": faixa_normal_30d,
        "fora_do_normal": fora_do_normal,
        "mudou_nas_ultimas_2_semanas": mudou_2s,
        "mudanca_2_semanas_pct": mudou_2s_pct,
        "limpeza": {
            "linhas_entrada": meta["rows_in"],
            "linhas_saida": meta["rows_out"],
            "tempo_invalido_removido": meta["invalid_time"],
            "duplicados_removidos": meta["removed_duplicates"],
            "picos_ajustados": meta["clamped_points"],
            "pontos_preenchidos": meta["filled_points"],
        },
        "previsao_ativa": True,
        "horizonte_previsao": 0,
        "previsao_curta": previsao_curta,
        "limite_da_previsao": obs_previsao,
        "previsao_texto": previsao_texto,
        "anormalidade_score": anormalidade,
    }


def resolve_dataset_path(dataset: str, year: int) -> Path:
    config_path = Path(__file__).resolve().parents[1] / "data_sources.json"
    if not config_path.exists():
        raise FileNotFoundError("data_sources.json not found in repo root.")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    source = config.get("ONS")
    if not source:
        raise ValueError("ONS source not found in data_sources.json")

    dataset_cfg = source.get(dataset)
    if not dataset_cfg:
        raise ValueError(f"Dataset not found in config: {dataset}")

    url_template = dataset_cfg.get("url_template")
    if not url_template:
        raise ValueError(f"Missing url_template for dataset: {dataset}")

    filename = Path(url_template.format(year=year)).name
    return Path(__file__).resolve().parents[1] / "data" / "raw" / "ONS" / dataset / filename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SPA minimal runner")
    parser.add_argument("--input", type=str, help="Path to input CSV")
    parser.add_argument("--time-col", type=str, required=True)
    parser.add_argument("--value-col", type=str, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--year", type=int)
    parser.add_argument("--source", type=str)
    parser.add_argument("--ons-mode", type=str, default="sum", choices=["sum", "select"])
    parser.add_argument("--ons-filter", action="append", default=[])
    parser.add_argument("--limpar", action="store_true")
    parser.add_argument("--limite_pico", type=float, default=6.0)
    parser.add_argument(
        "--preencher",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--remover_repetidos",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--prever", type=int, default=0)
    parser.add_argument(
        "--metodo_previsao",
        type=str,
        default="media_recente",
        choices=["media_recente", "tendencia_curta"],
    )
    parser.add_argument("--pdf", action="store_true", help="Generate PDF report")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    ons_filters = {}
    for raw_filter in args.ons_filter:
        if "=" not in raw_filter:
            raise ValueError(f"Invalid --ons-filter '{raw_filter}', use KEY=VALUE")
        key, value = raw_filter.split("=", 1)
        ons_filters[key] = value

    if args.input:
        input_path = Path(args.input)
    elif args.dataset and args.year:
        input_path = resolve_dataset_path(args.dataset, args.year)
    else:
        raise ValueError("Provide --input or both --dataset and --year.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.source == "ONS":
        raw_df = pd.read_csv(input_path, sep=None, engine="python")
        regioes_presentes, _ = _detectar_regioes(raw_df)
        subsystems = []
        for regiao in regioes_presentes:
            serie = normalize_ons(
                raw_df,
                time_col=args.time_col,
                value_col=args.value_col,
                mode="select",
                select_filters={"subsistema": regiao},
            )
            processed_df, meta, time_col, value_col = preprocess(
                serie,
                "time",
                "value",
                source=None,
                limpar=args.limpar,
                limite_pico=args.limite_pico,
                preencher=args.preencher,
                remover_repetidos=args.remover_repetidos,
            )
            feats = compute_features(processed_df, time_col, value_col)
            diagnostics = run_diagnostics(processed_df, value_col, feats["rolling_std"])
            processed_output = processed_df.copy()
            processed_output["rolling_std"] = feats["rolling_std"]
            safe = regiao.replace("/", "_").replace(" ", "_")
            processed_output.to_csv(outdir / f"processed_{safe}.csv", index=False)

            forecast_df, obs_previsao = forecast_series(
                processed_df,
                time_col,
                value_col,
                args.prever,
                args.metodo_previsao,
                meta["dt_seconds"],
            )
            if args.prever > 0:
                forecast_df.to_csv(outdir / f"forecast_{safe}.csv", index=False)

            previsao_curta = "Previsão desativada."
            if args.prever > 0 and not forecast_df.empty:
                valor_ultimo = float(processed_df[value_col].iloc[-1])
                prev_min = float(forecast_df["value_previsto"].min())
                prev_max = float(forecast_df["value_previsto"].max())
                if valor_ultimo != 0:
                    pct_min = (prev_min - valor_ultimo) / valor_ultimo * 100
                    pct_max = (prev_max - valor_ultimo) / valor_ultimo * 100
                    previsao_curta = (
                        f"Entre {_format_percent(pct_min)} e {_format_percent(pct_max)} "
                        f"nos próximos {args.prever} pontos."
                    )
                else:
                    previsao_curta = "Previsão gerada, mas sem base para comparar em porcentagem."

            previsao_texto = (
                f"A previsão curta sugere {previsao_curta.lower()} "
                "Ela usa apenas o comportamento recente e serve como referência rápida. "
                "Se o sistema mudar de forma inesperada, essa projeção pode falhar."
            )

            passo_de_tempo, passo_texto = _passo_texto(meta["dt_seconds"])
            summary = _build_summary(
                processed_df,
                value_col,
                feats,
                diagnostics,
                meta,
                passo_de_tempo,
                passo_texto,
                regiao,
                "select",
                previsao_curta,
                obs_previsao,
                previsao_texto,
            )
            summary["previsao_ativa"] = args.prever > 0
            summary["horizonte_previsao"] = args.prever
            summary["regiao_analisada"] = regiao
            (outdir / f"summary_{safe}.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            subsystems.append(
                {
                    "nome": regiao,
                    "df": processed_df,
                    "forecast": forecast_df,
                    "summary": summary,
                }
            )

        todas_datas = pd.concat([s["df"]["time"] for s in subsystems]).dropna()
        data_inicial = todas_datas.min()
        data_final = todas_datas.max()
        total_de_dias = int(todas_datas.dt.date.nunique())

        comparacao_vol = {s["nome"]: s["summary"]["nivel_de_ruido"] for s in subsystems}
        comparacao_mudanca = {
            s["nome"]: s["summary"]["mudanca_2_semanas_pct"] for s in subsystems
        }
        anormalidade = {
            s["nome"]: s["summary"]["anormalidade_score"] for s in subsystems
        }

        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        placar = []
        for sub in subsystems:
            df_mes = sub["df"].copy()
            df_mes["month"] = pd.to_datetime(df_mes["time"]).dt.month
            monthly = df_mes.groupby("month")["value"].mean()
            media_anual = float(df_mes["value"].mean())
            variabilidade = float(df_mes["value"].std())
            if not monthly.empty:
                mes_pico_idx = int(monthly.idxmax())
                mes_vale_idx = int(monthly.idxmin())
                mes_pico = meses[mes_pico_idx - 1]
                mes_vale = meses[mes_vale_idx - 1]
            else:
                mes_pico = "N/A"
                mes_vale = "N/A"
            placar.append(
                {
                    "regiao": _infer_region_key(sub["nome"]),
                    "media_anual": media_anual,
                    "mes_pico": mes_pico,
                    "mes_vale": mes_vale,
                    "variabilidade": variabilidade,
                }
            )

        mais_volatil = max(comparacao_vol, key=comparacao_vol.get) if comparacao_vol else "nao identificado"
        maior_mudanca = None
        if comparacao_mudanca:
            maior_mudanca = max(
                comparacao_mudanca.items(),
                key=lambda item: abs(item[1]) if item[1] is not None else -1,
            )[0]

        sintese = (
            "A síntese do sistema é baseada no comportamento individual de cada subsistema. "
            f"O subsistema com maior variabilidade recente é {mais_volatil}. "
        )
        if maior_mudanca:
            sintese += f"A maior mudança recente apareceu em {maior_mudanca}. "
        sintese += (
            "Essa leitura é mais confiável do que uma soma simples, "
            "porque preserva diferenças regionais importantes."
        )

        system_summary = {
            "o_que_e_dado": (
                "Este relatório analisa a demanda média diária de energia elétrica por subsistema. "
                "A carga elétrica indica quanta energia o sistema precisou atender, medida em MWmed."
            ),
            "o_que_e_subsistema": (
                "Subsistema é uma divisão regional do sistema elétrico. "
                "Cada subsistema tem comportamento próprio e pode variar de forma independente."
            ),
            "periodo_analisado": (
                f"O período analisado vai de {data_inicial.strftime('%d/%m/%Y')} "
                f"até {data_final.strftime('%d/%m/%Y')}, totalizando {total_de_dias} dias."
            ),
            "subsistemas": regioes_presentes,
            "sintese_sistema": sintese,
            "comparacao_volatilidade": comparacao_vol,
            "comparacao_mudancas": comparacao_mudanca,
            "anormalidade_por_subsistema": anormalidade,
            "placar_subsistemas": placar,
        }

        (outdir / "summary_system.json").write_text(
            json.dumps(system_summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (outdir / "placar_subsistemas.json").write_text(
            json.dumps(placar, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        if args.pdf:
            generate_report(system_summary, subsystems, outdir / "report.pdf")
        return

    # Fluxo padrão para dados não ONS (mantém comportamento simples)
    df, time_col, value_col = load_dataset(input_path, args.time_col, args.value_col)
    processed_df, meta, time_col, value_col = preprocess(
        df,
        time_col,
        value_col,
        source=args.source,
        ons_mode=args.ons_mode,
        ons_filters=ons_filters if ons_filters else None,
        limpar=args.limpar,
        limite_pico=args.limite_pico,
        preencher=args.preencher,
        remover_repetidos=args.remover_repetidos,
    )
    feats = compute_features(processed_df, time_col, value_col)
    diagnostics = run_diagnostics(processed_df, value_col, feats["rolling_std"])
    processed_output = processed_df.copy()
    processed_output["rolling_std"] = feats["rolling_std"]
    processed_output.to_csv(outdir / "processed.csv", index=False)

    forecast_df, obs_previsao = forecast_series(
        processed_df,
        time_col,
        value_col,
        args.prever,
        args.metodo_previsao,
        meta["dt_seconds"],
    )
    if args.prever > 0:
        forecast_df.to_csv(outdir / "forecast.csv", index=False)

    previsao_curta = "Previsão desativada."
    if args.prever > 0 and not forecast_df.empty:
        valor_ultimo = float(processed_df[value_col].iloc[-1])
        prev_min = float(forecast_df["value_previsto"].min())
        prev_max = float(forecast_df["value_previsto"].max())
        if valor_ultimo != 0:
            pct_min = (prev_min - valor_ultimo) / valor_ultimo * 100
            pct_max = (prev_max - valor_ultimo) / valor_ultimo * 100
            previsao_curta = (
                f"Entre {_format_percent(pct_min)} e {_format_percent(pct_max)} "
                f"nos próximos {args.prever} pontos."
            )

    previsao_texto = (
        f"A previsão curta sugere {previsao_curta.lower()} "
        "Ela usa apenas o comportamento recente e serve como referência rápida. "
        "Se o sistema mudar de forma inesperada, essa projeção pode falhar."
    )

    passo_de_tempo, passo_texto = _passo_texto(meta["dt_seconds"])
    summary = _build_summary(
        processed_df,
        value_col,
        feats,
        diagnostics,
        meta,
        passo_de_tempo,
        passo_texto,
        "nao_aplicavel",
        "sum",
        previsao_curta,
        obs_previsao,
        previsao_texto,
    )
    summary["previsao_ativa"] = args.prever > 0
    summary["horizonte_previsao"] = args.prever
    (outdir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if args.pdf:
        system_summary = {
            "o_que_e_dado": summary.get("o_que_e_esse_numero", ""),
            "o_que_e_subsistema": "Não se aplica para este conjunto de dados.",
            "periodo_analisado": summary.get("periodo_analisado", ""),
            "subsistemas": ["total"],
            "sintese_sistema": summary.get("situacao_atual", ""),
            "comparacao_volatilidade": {"total": summary.get("nivel_de_ruido")},
            "comparacao_mudancas": {"total": summary.get("mudanca_2_semanas_pct")},
            "anormalidade_por_subsistema": {"total": summary.get("anormalidade_score")},
        }
        generate_report(system_summary, [{"nome": "total", "df": processed_df, "forecast": forecast_df, "summary": summary}], outdir / "report.pdf")


if __name__ == "__main__":
    run()
