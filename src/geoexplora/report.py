"""Relatório técnico (PDF) de uma análise do GeoExplora IA."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer
from shapely.geometry import shape

from terravisao.report import pdf as base

from . import __version__, geophysics, ree
from .analysis import CLASS_LABEL, Analysis

C_BAIXA, C_MODERADA, C_ELEVADA = "#5E7A63", "#C9A227", "#B4532A"
CLASS_COLOR = {"baixa": C_BAIXA, "moderada": C_MODERADA, "elevada": C_ELEVADA}
INK = "#1C1B18"
DISCLAIMER = (
    "Esta análise classifica amostras e grelhas fornecidas pelo utilizador. As classes são "
    "relativas ao conjunto de dados, não são teores económicos nem recursos. Não confirma a "
    "existência de mineralização, não substitui o trabalho de campo nem a sondagem."
)


def _jpeg(fig: Any) -> bytes:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="jpeg",
        dpi=125,
        bbox_inches="tight",
        facecolor="white",
        pil_kwargs={"quality": 88, "optimize": True},
    )
    plt.close(fig)
    return buf.getvalue()


def _axes(a: Analysis, title: str) -> tuple[Any, Any]:
    df = a.points.df
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    pad = 0.04 * max(np.ptp(df["x"]), np.ptp(df["y"]))
    ax.set_xlim(df["x"].min() - pad, df["x"].max() + pad)
    ax.set_ylim(df["y"].min() - pad, df["y"].max() + pad)
    ax.set_aspect("equal")
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}")
    ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_major_formatter(fmt)
    ax.tick_params(labelsize=7, colors="#6B675D")
    ax.set_xlabel(f"Este (km, EPSG:{a.points.epsg})", fontsize=7, color="#6B675D")
    ax.set_ylabel("Norte (km)", fontsize=7, color="#6B675D")
    for s in ax.spines.values():
        s.set_color("#D8D2C4")
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=8)
    return fig, ax


def _scalebar(ax: Any) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    length = max(n for n in (500, 1000, 2000, 5000) if n <= (x1 - x0) / 3 or n == 500)
    x, y = x0 + (x1 - x0) * 0.04, y0 + (y1 - y0) * 0.05
    ax.plot([x, x + length], [y, y], color=INK, lw=2.5, solid_capstyle="butt", zorder=9)
    ax.text(
        x,
        y + (y1 - y0) * 0.015,
        f"{length // 1000} km" if length >= 1000 else f"{length} m",
        fontsize=7,
        color=INK,
        zorder=9,
    )


def _zone_outlines(ax: Any, a: Analysis) -> None:
    to_utm = Transformer.from_crs(4326, a.points.epsg, always_xy=True)
    for z in a.zones:
        import shapely

        def project(c: np.ndarray) -> np.ndarray:
            x, y = to_utm.transform(c[:, 0], c[:, 1])
            return np.column_stack([x, y])

        poly = shapely.transform(shape(z.polygon), project)
        for p in getattr(poly, "geoms", [poly]):
            x, y = p.exterior.xy
            ax.plot(
                x,
                y,
                color=INK,
                lw=1.6 if z.significant else 1.0,
                ls="-" if z.significant else (0, (4, 3)),
                zorder=6,
            )
        c = poly.representative_point()
        ax.annotate(
            z.id,
            (c.x, c.y),
            fontsize=8,
            fontweight="bold",
            color="white",
            ha="center",
            va="center",
            zorder=7,
            bbox={
                "boxstyle": "circle,pad=0.2",
                "fc": INK if z.significant else "#6B675D",
                "ec": "none",
            },
        )


def map_classes(a: Analysis) -> bytes:
    fig, ax = _axes(a, "Amostras por classe de anomalia e zonas")
    df = a.points.df
    for cls in ("baixa", "moderada", "elevada"):
        sel = df[df["classe"] == cls]
        ax.scatter(
            sel["x"],
            sel["y"],
            s=14 if cls != "elevada" else 22,
            c=CLASS_COLOR[cls],
            edgecolors="white",
            linewidths=0.4,
            label=f"{CLASS_LABEL[cls]} ({len(sel)})",
            zorder=4,
        )
    _zone_outlines(ax, a)
    _scalebar(ax)
    ax.legend(loc="upper right", fontsize=7, frameon=True, framealpha=0.9, edgecolor="#D8D2C4")
    return _jpeg(fig)


def map_surface(a: Analysis) -> bytes:
    fig, ax = _axes(a, f"Superfície interpolada: {a.treo_label}")
    s = a.surface
    rows, cols = s.array.shape
    extent = (s.x0, s.x0 + cols * s.dx, s.y1 - rows * s.dx, s.y1)
    lo, hi = np.nanpercentile(s.array, [2, 98])
    im = ax.imshow(s.array, extent=extent, cmap="YlOrBr", vmin=lo, vmax=hi, alpha=0.9, zorder=2)
    df = a.points.df
    ax.scatter(df["x"], df["y"], s=3, c=INK, alpha=0.5, zorder=4)
    _zone_outlines(ax, a)
    _scalebar(ax)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("ppm", fontsize=7)
    cbar.ax.tick_params(labelsize=7)
    return _jpeg(fig)


def map_grid(
    a: Analysis,
    name: str,
    grid_array: np.ndarray,
    extent: tuple[float, float, float, float],
    title: str,
) -> bytes:
    fig, ax = _axes(a, title)
    lo, hi = np.nanpercentile(grid_array, [2, 98])
    im = ax.imshow(
        grid_array,
        extent=extent,
        cmap="RdBu_r" if lo < 0 < hi else "viridis",
        vmin=lo,
        vmax=hi,
        zorder=2,
    )
    df = a.points.df
    ax.scatter(df["x"], df["y"], s=3, c="black", alpha=0.35, zorder=4)
    _scalebar(ax)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=7)
    return _jpeg(fig)


def histogram(a: Analysis) -> bytes:
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    vals = a.points.df["metrica_ppm"]
    ax.hist(vals, bins=30, color="#D8D2C4", edgecolor="white")
    for name, color in (("moderada", C_MODERADA), ("elevada", C_ELEVADA)):
        ax.axvline(a.thresholds[name], color=color, lw=1.6)
        ax.text(
            a.thresholds[name],
            ax.get_ylim()[1] * 0.92,
            f" {CLASS_LABEL[name]}",
            color=color,
            fontsize=8,
        )
    ax.set_xlabel(f"{a.treo_label} (ppm)", fontsize=8)
    ax.set_ylabel("Amostras", fontsize=8)
    ax.tick_params(labelsize=7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _jpeg(fig)


def _footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(base.SOFT)
    canvas.drawString(
        2 * cm,
        1.2 * cm,
        "GeoExplora IA · relatório técnico · ferramenta de apoio, não confirma mineralização",
    )
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(base.LINE)
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def generate_analysis_report(a: Analysis, out: Path, narrative: str | None = None) -> Path:
    """PDF técnico da análise. `narrative` é o texto de interpretação (automático ou da IA)."""
    from .assistant import interpretation

    p, tbl, n = base._p, base._table, base._n
    s = a.summary()
    pts = a.points
    story: list[Any] = [
        p("Relatório técnico de análise", "title"),
        p(
            f"{pts.title or 'Conjunto de dados'} · gerado em {datetime.now():%d/%m/%Y %H:%M} · "
            f"{len(pts.df)} amostras · {a.treo_label}",
            "sub",
        ),
    ]
    if pts.fictitious:
        story += [
            Spacer(1, 6),
            p(
                '<font color="#B4532A"><b>DADOS FICTÍCIOS: demonstração. '
                "Os resultados não representam mineralização real.</b></font>",
                "body",
            ),
        ]
    story += [Spacer(1, 8), p("Interpretação", "h1")]
    for para in (narrative or interpretation(s)).split("\n\n"):
        story.append(p(para.replace("\n", "<br/>"), "body"))
        story.append(Spacer(1, 4))
    story += [p(DISCLAIMER, "small")]
    if a.warnings:
        story += [p("Avisos", "h2")] + [p("• " + w, "small") for w in dict.fromkeys(a.warnings)]

    # Mapas
    story += [PageBreak(), p("Mapas", "h1"), base._img(map_classes(a), 15.0)]
    story += [PageBreak(), base._img(map_surface(a), 15.0)]
    grid_maps: list[tuple[str, bytes]] = []
    for name, g in a.grids.items():
        x0, y0, x1, y1 = g.bounds()
        grid_maps.append((name, map_grid(a, name, g.array, (x0, x1, y0, y1), name)))
        for dname, arr in geophysics.derivatives(g.array, g.resolution).items():
            if dname in ("Sinal analítico", "Primeira derivada vertical"):
                grid_maps.append(
                    (
                        f"{name}: {dname}",
                        map_grid(a, name, arr, (x0, x1, y0, y1), f"{name}: {dname}"),
                    )
                )
    if grid_maps:
        story += [
            PageBreak(),
            p("Mapas geofísicos e derivadas", "h1"),
            p(
                "As derivadas realçam as fontes: o sinal analítico é máximo sobre o corpo, a "
                "primeira derivada vertical delimita as bordas. Calculadas por FFT na grelha carregada.",
                "small",
            ),
            Spacer(1, 6),
        ]
        for _, png in grid_maps:
            story.append(base._img(png, 11.5))

    # Estatística
    story += [PageBreak(), p("Estatística descritiva", "h1")]
    rows: list[list[Any]] = [["Variável", "Mínimo", "Mediana", "Média", "Máximo"]]
    df = pts.df
    cols = [f"{e}_ppm" for e in ree.available(pts.elements)] or [f"{e}_ppm" for e in pts.elements]
    for c in [*cols, "metrica_ppm"]:
        v = df[c]
        label = a.treo_label if c == "metrica_ppm" else c.replace("_ppm", " (ppm)")
        rows.append([label, n(v.min()), n(v.median()), n(v.mean()), n(v.max())])
    story += [
        tbl(rows, [6 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm]),
        Spacer(1, 6),
        base._img(histogram(a), 14.5),
    ]
    story.append(
        p(
            f"Limiares ({a.params.method}): moderada ≥ {n(a.thresholds['moderada'])} ppm; "
            f"elevada ≥ {n(a.thresholds['elevada'])} ppm.",
            "small",
        )
    )

    # Zonas
    story.append(p("Zonas de interesse", "h1"))
    if a.zones:
        zr: list[list[Any]] = [
            [
                "Zona",
                "Amostras",
                "Área",
                "Média (ppm)",
                "Máx. (ppm)",
                "NdPr/TREO",
                "Maior que o acaso",
            ]
        ]
        for z in a.zones:
            zr.append(
                [
                    p(f"<b>{z.id}</b>", "cell"),
                    str(z.n_samples),
                    f"{n(z.area_km2)} km²",
                    n(z.mean_value_ppm, 0),
                    n(z.max_value_ppm, 0),
                    "—" if z.ndpr_share is None else f"{n(z.ndpr_share * 100)} %",
                    "sim" if z.significant else "não",
                ]
            )
        story.append(tbl(zr, [1.3 * cm, 2 * cm, 2.4 * cm, 2.6 * cm, 2.4 * cm, 2.3 * cm, 2.8 * cm]))
        story.append(
            p(
                "Uma zona só é «maior que o acaso» se tiver mais amostras elevadas do que 95 % "
                "das redistribuições aleatórias das mesmas amostras (teste de permutação).",
                "small",
            )
        )
    else:
        story.append(p("Nenhuma zona delimitada.", "small"))

    # Relações e modelo
    story.append(p("Relação com a geofísica", "h1"))
    if a.correlations:
        story.append(
            tbl(
                [["Variável", "Spearman", "p", "Leitura", "n"]]
                + [
                    [
                        r["variavel"],
                        n(r["rho_spearman"], 2),
                        n(r["p_valor"], 4),
                        r["leitura"],
                        str(r["n"]),
                    ]
                    for r in a.correlations
                ],
                [5.4 * cm, 2.2 * cm, 2.2 * cm, 4.6 * cm, 1.8 * cm],
            )
        )
    else:
        story.append(p("Sem variáveis geofísicas para comparar.", "small"))
    m = a.model
    story.append(p("Modelo de apoio (Random Forest)", "h2"))
    if m.get("executado"):
        story.append(p(f"{m['leitura']}", "body"))
        story.append(
            p(
                f"Exatidão {n(m['exatidao'] * 100, 0)} % (acaso {n(m['acaso'] * 100, 0)} %), "
                f"p = {n(m['p_valor_vs_acaso'], 3)}; {m['n']} amostras; validação cruzada por "
                "blocos espaciais. Importância por permutação: "
                + ", ".join(f"{k} {n(v, 3)}" for k, v in m["importancia"].items())
                + ".",
                "small",
            )
        )
    else:
        story.append(p(f"Não executado: {m.get('motivo', '')}", "small"))

    # Metodologia e limitações
    story.append(
        KeepTogether(
            [
                p("Metodologia", "h1"),
                p(
                    "As amostras são convertidas para UTM e a métrica é calculada por amostra (TREO a partir "
                    "dos elementos presentes, com factores estequiométricos padrão de elemento para óxido; "
                    "NdPr/TREO para ímanes permanentes). As classes (baixa, moderada, elevada) usam quantis do "
                    "próprio conjunto ou desvios em escala logarítmica. A superfície é interpolada por inverso "
                    "da distância. As zonas agrupam espacialmente as amostras elevadas (DBSCAN) e são testadas "
                    "contra o acaso por permutação. As grelhas geofísicas são amostradas nos pontos e "
                    "derivadas por FFT. O modelo é validado por blocos espaciais.",
                    "body",
                ),
            ]
        )
    )
    story += [p("Limitações", "h1")] + [
        p("• " + t, "body")
        for t in (
            "As classes são relativas ao conjunto de dados: não são teores económicos nem categorias de recursos.",
            "O TREO é parcial quando faltam elementos e subestima o valor total.",
            "Interpolação e zonas dependem da malha de amostragem; zonas sem amostras de apoio não são fiáveis.",
            "Correlação não é causa; o modelo só é útil se superar o acaso com validação espacial.",
            "A redução ao pólo (RTP) não está incluída; as derivadas assumem grelha regular em metros.",
        )
    ]
    story.append(Spacer(1, 6))
    story.append(KeepTogether([p("Aviso", "h2"), p(DISCLAIMER, "body")]))
    story.append(
        KeepTogether(
            [
                p("Anexo — parâmetros", "h1"),
                p(
                    f"GeoExplora IA {__version__} · método {a.params.method} · quantis "
                    f"{a.params.q_moderada}/{a.params.q_elevada} · agrupamento mín. {a.params.cluster_min_samples} amostras · "
                    f"superfície {a.params.surface_cells} células · ficheiro: {pts.source or 'demonstração'}",
                    "small",
                ),
            ]
        )
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.2 * cm,
        title=f"GeoExplora IA — {pts.title}",
        author="GeoExplora IA",
    ).build(story, onFirstPage=_footer, onLaterPages=_footer)
    return out
