from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Iterable

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union


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


def _iter_polygons(geom) -> Iterable:
    if geom.geom_type == "Polygon":
        yield geom
    elif geom.geom_type == "MultiPolygon":
        for part in geom.geoms:
            yield part


def _dissolve_regioes(geojson_path: Path) -> Dict[str, object]:
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    regiao_id_map = {
        "1": "S",       # Sul
        "2": "SE/CO",   # Sudeste
        "3": "N",       # Norte
        "4": "NE",      # Nordeste
        "5": "SE/CO",   # Centro-Oeste
    }
    groups: Dict[str, List[object]] = {"N": [], "NE": [], "SE/CO": [], "S": []}

    for feature in data["features"]:
        props = feature.get("properties", {})
        regiao_id = str(props.get("regiao_id", ""))
        key = regiao_id_map.get(regiao_id)
        if not key:
            continue
        geom = shape(feature["geometry"])
        groups[key].append(geom)

    dissolved = {}
    for key, geoms in groups.items():
        if not geoms:
            continue
        dissolved[key] = unary_union(geoms)
    return dissolved


def _mapa_brasil_regioes(ax: plt.Axes, geojson_path: Path, medias: Dict[str, float]) -> None:
    regions = _dissolve_regioes(geojson_path)

    values = [v for v in medias.values() if v is not None]
    vmin = min(values) if values else 0
    vmax = max(values) if values else 1
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap("YlOrRd")

    for key, geom in regions.items():
        valor = medias.get(key, None)
        cor = cmap(norm(valor)) if valor is not None else (0.9, 0.9, 0.9, 1.0)
        for poly in _iter_polygons(geom):
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color=cor, edgecolor="black", linewidth=1.6)
        centro = geom.representative_point()
        label = f"{key}\n{valor:.0f} MWmed" if valor is not None else key
        ax.text(centro.x, centro.y, label, ha="center", va="center", fontsize=11, weight="bold")

    ax.set_aspect("equal")
    ax.axis("off")

    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("MWmed (baixo → alto)")


def _save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")


def generate_report(system_summary: Dict[str, object], subsystems: List[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plots_dir = output_path.parent / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    medias = {}
    variacoes = {}
    for sub in subsystems:
        key = _infer_region_key(sub["nome"])
        medias[key] = float(sub["df"]["value"].mean())
        variacoes[key] = float(sub["df"]["value"].std())

    maior_media = max(medias, key=medias.get) if medias else "N/A"
    maior_variacao = max(variacoes, key=variacoes.get) if variacoes else "N/A"

    geojson_path = Path(__file__).resolve().parents[1] / "data" / "geo" / "br_uf.geojson"

    with PdfPages(output_path) as pdf:
        # Página 1 — Capa
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "SPA Energy Visual Intelligence", fontsize=18, weight="bold", va="top")
        fig.text(
            0.08,
            0.90,
            "Diagnóstico visual da demanda elétrica no Brasil (dados ONS)",
            fontsize=12,
            va="top",
        )
        fig.text(
            0.08,
            0.86,
            system_summary.get("periodo_analisado", ""),
            fontsize=11,
            wrap=True,
            va="top",
        )
        fig.text(
            0.08,
            0.80,
            "Transformando dados brutos do sistema elétrico em diagnóstico claro.",
            fontsize=12,
            style="italic",
            va="top",
        )
        ax_map = fig.add_axes([0.08, 0.12, 0.84, 0.65])
        _mapa_brasil_regioes(ax_map, geojson_path, medias)
        _save_fig(fig, plots_dir / "mapa_brasil_regioes.png")
        pdf.savefig(fig)
        plt.close(fig)

        # Página 2 — O problema
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "O problema", fontsize=16, weight="bold", va="top")
        fig.text(
            0.08,
            0.90,
            "Dados de energia são extensos, ruidosos e difíceis de interpretar quando vistos apenas "
            "como uma série única. Decisões operacionais exigem visão global, mas também leitura regional, "
            "porque o comportamento do Norte não é o mesmo do Sudeste/Centro-Oeste.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        fig.text(
            0.08,
            0.78,
            "Este relatório foi pensado para analistas, gestores e equipes de planejamento e operações "
            "que precisam entender rapidamente onde a demanda se concentra e onde surgem variações relevantes.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        pdf.savefig(fig)
        plt.close(fig)

        # Página 3 — O método
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "O método", fontsize=16, weight="bold", va="top")
        fig.text(
            0.08,
            0.90,
            "O diagnóstico segue três passos simples e transparentes: primeiro, analisamos cada "
            "subsistema separadamente; depois, comparamos as regiões; e por fim sintetizamos o sistema "
            "como um todo a partir desses comportamentos individuais.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        fig.text(
            0.08,
            0.78,
            "Este não é um modelo de previsão mágica. É um diagnóstico operacional que torna visíveis "
            "padrões e diferenças regionais para orientar decisões.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        pdf.savefig(fig)
        plt.close(fig)

        # Página 4 — Visão do Brasil
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "Visão do Brasil", fontsize=16, weight="bold", va="top")
        fig.text(
            0.08,
            0.90,
            "O mapa destaca onde a demanda se concentra. A região SE/CO reúne Sudeste e Centro-Oeste "
            "e normalmente carrega a maior parte da carga elétrica do país. As cores mais fortes indicam "
            "maior demanda média anual.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        ax_map = fig.add_axes([0.08, 0.12, 0.84, 0.70])
        _mapa_brasil_regioes(ax_map, geojson_path, medias)
        pdf.savefig(fig)
        plt.close(fig)

        # Página 5 — Comparação regional
        placar = system_summary.get("placar_subsistemas", [])
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 11), constrained_layout=True)
        fig.text(0.08, 0.95, "Comparação regional", fontsize=16, weight="bold", va="top")
        fig.text(
            0.08,
            0.91,
            "A curva mensal evidencia diferenças sazonais entre regiões. "
            "O gráfico de barras resume a média anual e deixa claro quem concentra a demanda.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        month_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        for sub in subsystems:
            df = sub["df"].copy()
            df["month"] = pd.to_datetime(df["time"]).dt.month
            monthly = df.groupby("month")["value"].mean()
            axes[0].plot(range(1, 13), [monthly.get(m, np.nan) for m in range(1, 13)], label=sub["nome"])
        axes[0].set_xticks(range(1, 13))
        axes[0].set_xticklabels(month_labels)
        axes[0].set_ylabel("MWmed")
        axes[0].set_title("Média mensal por subsistema")
        axes[0].legend(loc="upper left")

        nomes = [item["regiao"] for item in placar]
        medias_bar = [item["media_anual"] for item in placar]
        axes[1].bar(nomes, medias_bar, color="tab:orange")
        axes[1].set_ylabel("MWmed")
        axes[1].set_title("Média anual por subsistema")
        pdf.savefig(fig)
        plt.close(fig)

        # Páginas 6–9 — Detalhe por subsistema
        for sub in subsystems:
            summary = sub["summary"]
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.08, 0.95, f"Subsistema — {sub['nome']}", fontsize=16, weight="bold", va="top")
            fig.text(
                0.08,
                0.90,
                "Esta leitura destaca o comportamento normal da região, os pontos que chamam atenção "
                "no ano analisado e o que merece monitoramento mais próximo.",
                fontsize=11,
                wrap=True,
                va="top",
            )

            ax1 = fig.add_axes([0.08, 0.56, 0.84, 0.22])
            ax1.plot(sub["df"]["time"], sub["df"]["value"], linewidth=1)
            ax1.set_title("Série diária do ano")
            ax1.set_ylabel("MWmed")

            ax2 = fig.add_axes([0.08, 0.28, 0.84, 0.22])
            janela = sub["df"].tail(60)
            ax2.plot(janela["time"], janela["value"], linewidth=1, label="observado")
            forecast = sub["forecast"]
            if forecast is not None and not forecast.empty:
                ax2.plot(
                    forecast["time"],
                    forecast["value_previsto"],
                    linewidth=1,
                    linestyle="--",
                    label="previsão curta",
                )
            ax2.set_title("Últimos 60 dias e previsão")
            ax2.set_ylabel("MWmed")
            ax2.legend(loc="upper left")

            bullets = [
                f"O que é normal: {summary.get('comparacao_30d', '')}",
                f"O que chama atenção: {summary.get('mudancas_recentes', '')}",
                "O que monitorar: acompanhar os próximos dias e confirmar se o padrão se mantém.",
            ]
            fig.text(0.08, 0.20, "\n".join([f"- {b}" for b in bullets]), fontsize=11, wrap=True, va="top")

            pdf.savefig(fig)
            plt.close(fig)

        # Página final — Conclusões e próximos passos
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "Conclusões e próximos passos", fontsize=16, weight="bold", va="top")
        conclusoes = [
            f"O Sudeste/Centro-Oeste concentra a maior parte da demanda elétrica do país.",
            f"A região com maior variabilidade é {maior_variacao}, indicando maior instabilidade relativa.",
            "A comparação regional evita que sinais locais se percam em uma média nacional.",
            "Mudanças regionais antecipam pressões no sistema como um todo.",
            "Diagnóstico visual reduz o tempo entre dado bruto e decisão prática.",
        ]
        recomendacoes = [
            "Priorizar monitoramento em regiões de maior variabilidade ao longo do ano.",
            "Usar a comparação mensal para antecipar períodos de pico regional.",
            "Integrar este diagnóstico ao planejamento operacional.",
        ]
        fig.text(0.08, 0.88, "Principais conclusões:", fontsize=12, weight="bold", va="top")
        fig.text(0.10, 0.84, "\n".join([f"- {c}" for c in conclusoes]), fontsize=11, wrap=True, va="top")
        fig.text(0.08, 0.56, "Recomendações práticas:", fontsize=12, weight="bold", va="top")
        fig.text(0.10, 0.52, "\n".join([f"- {r}" for r in recomendacoes]), fontsize=11, wrap=True, va="top")
        fig.text(
            0.08,
            0.20,
            "Este projeto demonstra como métodos físicos e estatísticos podem gerar valor prático a partir de dados reais.",
            fontsize=11,
            wrap=True,
            va="top",
        )
        pdf.savefig(fig)
        plt.close(fig)
