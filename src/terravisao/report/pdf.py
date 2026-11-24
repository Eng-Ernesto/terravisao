"""Relatório PDF de triagem (docs/06 §4). Lê uma pasta de exportação do pipeline."""

from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from shapely.geometry import shape

from .. import __version__
from ..aoi import area_km2
from ..config import DEFAULT_WEIGHTS, Target
from . import maps

INK = colors.HexColor("#1C1B18")
SOFT = colors.HexColor("#6B675D")
LINE = colors.HexColor("#D8D2C4")
OXIDE = colors.HexColor("#B4532A")
LEVEL = {"baixa": "baixa", "media": "média", "alta": "alta"}
LEVEL_COLOR = {"baixa": "#5E7A63", "media": "#C9A227", "alta": "#B4532A"}
TARGET_LABEL = {
    "terras_raras": "Terras raras",
    "cobre": "Cobre",
    "litio": "Lítio",
    "manganes": "Manganês",
}
LAYER_LABEL = {
    "iron_oxide": "Óxido de ferro",
    "ferrous": "Ferroso",
    "clay": "Alteração argilosa",
    "lithology": "Litologia",
    "lineament_density": "Densidade de lineamentos",
    "slope_inv": "Declive baixo",
    "twi": "Humidade do terreno (TWI)",
    "drainage_density_inv": "Drenagem esparsa",
    "ndvi": "Vegetação (NDVI)",
}
DISCLAIMER = (
    "Este resultado indica probabilidade com base em dados públicos de detecção remota "
    "(Sentinel-2, modelo digital de elevação e, quando disponível, mapas geológicos). "
    "Não confirma a existência de minerais ou de água subterrânea, não substitui o trabalho "
    "de campo do geofísico nem a sondagem. Utilize-o para decidir onde confirmar, "
    "não para decidir se investe."
)

STYLES = {
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=24, leading=28, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=SOFT),
    "h1": ParagraphStyle(
        "h1",
        fontName="Times-Bold",
        fontSize=15,
        leading=19,
        textColor=INK,
        spaceBefore=14,
        spaceAfter=6,
    ),
    "h2": ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=SOFT,
        spaceBefore=10,
        spaceAfter=4,
    ),
    "body": ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9.5, leading=14, textColor=INK, alignment=TA_LEFT
    ),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=11, textColor=SOFT),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=INK),
}


def _n(x: float, dec: int = 1) -> str:
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def _table(rows: list[list[Any]], widths: list[float], header: bool = True) -> Table:
    data = [[c if isinstance(c, Paragraph) else _p(str(c), "cell") for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]
    if header:
        style.append(("LINEBELOW", (0, 0), (-1, 0), 0.8, INK))
    t.setStyle(TableStyle(style))
    return t


def _chip(level: str) -> str:
    return f'<font color="{LEVEL_COLOR[level]}">●</font> {LEVEL[level]}'


def _footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SOFT)
    canvas.drawString(
        2 * cm,
        1.2 * cm,
        "TerraVisão · relatório de triagem · não confirma a presença de minerais ou água",
    )
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def _img(png: bytes, width_cm: float) -> Image:
    from PIL import Image as PILImage

    w, h = PILImage.open(io.BytesIO(png)).size
    return Image(io.BytesIO(png), width=width_cm * cm, height=width_cm * cm * h / w)


def generate_report(folder: Path, out: Path | None = None) -> Path:
    """Gera o PDF a partir de `folder` (run.json, GeoTIFF e GeoJSON). Devolve o caminho."""
    folder = Path(folder)
    run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    meta_file = folder / "meta.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    summary, prov, req = run["summary"], run["provenance"], run["request"]
    title = meta.get("title") or req.get("name") or folder.name
    geom = shape(req["geometry"])
    c = geom.centroid
    created = datetime.fromisoformat(prov["created_at"]).strftime("%d/%m/%Y %H:%M")
    area = area_km2(geom)
    out = out or folder / f"relatorio_{folder.name}.pdf"
    story: list[Any] = []

    # 1. Capa e resumo executivo
    story += [
        _p(title, "title"),
        _p(
            f"Relatório de triagem · gerado em {created} UTC · centro "
            f"{_n(abs(c.y), 3)}°{'S' if c.y < 0 else 'N'} {_n(abs(c.x), 3)}°{'W' if c.x < 0 else 'E'} · "
            f"área analisada {_n(area)} km²",
            "sub",
        ),
        Spacer(1, 10),
        _p("Resumo", "h1"),
    ]
    rows: list[list[Any]] = [
        ["Alvo", "Probabilidade", "Confiança dos dados", "Zonas", "Maior zona"]
    ]
    for t, r in summary["targets"].items():
        biggest = max((z["area_km2"] for z in r["zonas"]), default=0.0)
        rows.append(
            [
                TARGET_LABEL[t],
                _p(_chip(r["classe_final"]), "cell"),
                _p(_chip(r["confianca"]), "cell"),
                str(len(r["zonas"])),
                f"{_n(biggest * 100)} ha" if r["zonas"] else "—",
            ]
        )
    story.append(_table(rows, [4.2 * cm, 3.4 * cm, 4 * cm, 1.8 * cm, 3 * cm]))
    story += [Spacer(1, 8), _p(DISCLAIMER, "small")]
    if summary.get("warnings"):
        story += [_p("Avisos", "h2")]
        story += [_p("• " + w, "small") for w in dict.fromkeys(summary["warnings"])]
    first = next(iter(summary["targets"]), None)
    if first:
        overview = _img(
            maps.class_map(folder, first, f"{TARGET_LABEL[first]} — probabilidade e zonas"), 10.5
        )
        story.append(KeepTogether([_p("Visão geral", "h1"), overview]))

    # 2. Mapas e zonas por alvo
    for t, r in summary["targets"].items():
        story.append(PageBreak())
        story.append(_p(TARGET_LABEL[t], "h1"))
        story.append(
            _p(
                f"Probabilidade {_chip(r['classe_final'])} · confiança dos dados {_chip(r['confianca'])}",
                "body",
            )
        )
        story.append(Spacer(1, 6))
        story.append(
            _img(maps.class_map(folder, t, f"{TARGET_LABEL[t]} — probabilidade e zonas"), 15.5)
        )
        areas = r["area_por_classe_km2"]
        story.append(
            _p(
                "Área por classe: "
                + " · ".join(f"{LEVEL[k]} {_n(areas[k])} km²" for k in ("baixa", "media", "alta")),
                "small",
            )
        )
        zfile = folder / f"zones_{t}.geojson"
        props = (
            {
                f["properties"]["id"]: f["properties"]
                for f in json.loads(zfile.read_text(encoding="utf-8"))["features"]
            }
            if zfile.exists()
            else {}
        )
        story.append(_p("Zonas prioritárias", "h2"))
        if r["zonas"]:
            zrows: list[list[Any]] = [
                ["Zona", "Área", "Pontuação", "Principais camadas", "Método de campo sugerido"]
            ]
            for z in r["zonas"]:
                p = props.get(z["id"], {})
                top = sorted(
                    p.get("contributions", {}).items(), key=lambda kv: kv[1], reverse=True
                )[:3]
                zrows.append(
                    [
                        _p(f"<b>{z['id']}</b>", "cell"),
                        f"{_n(z['area_km2'] * 100)} ha",
                        _n(z["score_medio"], 2),
                        _p(", ".join(LAYER_LABEL.get(k, k) for k, _ in top) or "—", "cell"),
                        _p(p.get("recommendation", ""), "cell"),
                    ]
                )
            story.append(_table(zrows, [1.3 * cm, 2 * cm, 2 * cm, 5.4 * cm, 6.3 * cm]))
        else:
            story.append(_p("Nenhuma zona acima da área mínima de 5 ha.", "small"))

    # 3. Camadas de apoio
    support = [
        ("layer_iron_oxide", "Óxido de ferro (razão B04/B02)"),
        ("layer_clay", "Alteração argilosa (razão B11/B12)"),
        ("layer_slope", "Declive (graus)"),
        ("layer_ndvi", "Vegetação (NDVI)"),
    ]
    raw = [(label, maps.layer_map(folder, name, label)) for name, label in support]
    pngs = [(label, img) for label, img in raw if img is not None]
    if pngs:
        story.append(PageBreak())
        story.append(_p("Camadas de apoio", "h1"))
        story.append(
            _p(
                "Valores relativos à própria área analisada (percentis 2–98). Servem para "
                "interpretar a pontuação, não são medidas absolutas.",
                "small",
            )
        )
        story.append(Spacer(1, 6))
        for i in range(0, len(pngs), 2):
            cells = [_img(p, 8.3) for _, p in pngs[i : i + 2]]
            story.append(Table([cells], colWidths=[8.6 * cm] * len(cells), hAlign="LEFT"))

    # 4. Metodologia, qualidade, limitações
    story.append(PageBreak())
    story.append(_p("Metodologia", "h1"))
    story.append(
        _p(
            "O terreno é analisado sobre uma grelha de 20 m. Calculam-se índices espectrais a partir "
            "de um composto sem nuvens de imagens Sentinel-2 L2A da época seca (óxido de ferro, "
            "ferroso, alteração argilosa e NDVI) e derivadas do modelo digital de elevação Copernicus "
            "GLO-30 (declive, drenagem, humidade do terreno e densidade de lineamentos). Cada camada "
            "é normalizada entre 0 e 1 dentro da área e combinada numa soma ponderada por alvo. A "
            "pontuação é suavizada (100 m) e classificada em baixa (&lt; 0,40), média e alta "
            "(≥ 0,65). As zonas são manchas contínuas de classe alta com pelo menos 5 ha.",
            "body",
        )
    )
    story.append(_p("Pesos usados (pontos de partida, a calibrar com geofísico)", "h2"))
    layers = sorted({k for t in summary["targets"] for k in DEFAULT_WEIGHTS[Target(t)]})
    wrows: list[list[Any]] = [["Camada", *[TARGET_LABEL[t] for t in summary["targets"]]]]
    for k in layers:
        wrows.append(
            [LAYER_LABEL.get(k, k)]
            + [
                f"{DEFAULT_WEIGHTS[Target(t)].get(k, 0):.2f}".replace(".", ",")
                if DEFAULT_WEIGHTS[Target(t)].get(k)
                else "—"
                for t in summary["targets"]
            ]
        )
    ncol = len(wrows[0])
    story.append(_table(wrows, [5.2 * cm] + [(12 * cm) / (ncol - 1)] * (ncol - 1)))

    story.append(_p("Qualidade dos dados", "h1"))
    q = prov.get("layer_quality", {})
    qrows: list[list[Any]] = [["Fonte", "Fracção de píxeis válidos"]]
    qrows += [
        [{"sentinel2": "Sentinel-2", "dem": "Modelo de elevação"}.get(k, k), f"{_n(v * 100, 0)} %"]
        for k, v in q.items()
    ]
    story.append(_table(qrows, [6 * cm, 5 * cm]))

    story.append(_p("Limitações", "h1"))
    for text in (
        "A detecção remota vê a superfície, não o subsolo.",
        "Ouro e cobre não têm assinatura espectral directa: o resultado indica contexto favorável (alteração associada), não a presença do metal.",
        "Óxido de ferro também aparece em solos e lateritos sem minério; vegetação e solos cobertos reduzem a fiabilidade dos índices.",
        'A pontuação é relativa à área analisada: numa área pobre, o melhor local continua a parecer "alto".',
        "Os pesos são heurísticos e ainda não foram calibrados com dados de campo.",
        "Os lineamentos extraídos do modelo de elevação são candidatos a falhas, não falhas confirmadas.",
        "Sem mapa geológico, a confiança dos dados fica limitada a «média».",
    ):
        story.append(_p("• " + text, "body"))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([_p("Aviso", "h2"), _p(DISCLAIMER, "body")]))

    # 5. Anexo de proveniência
    annex: list[Any] = [_p("Anexo — proveniência", "h1")]
    scenes = prov.get("scenes", {}).get("sentinel2", [])
    annex.append(_p(f"Versão do pipeline: {prov.get('pipeline_version', __version__)}", "small"))
    annex.append(_p(f"Data de geração: {created} UTC", "small"))
    annex.append(_p("Cenas Sentinel-2 usadas: " + (", ".join(scenes) or "—"), "small"))
    cfg = prov.get("config_snapshot", {})
    annex.append(_p("Parâmetros: " + "; ".join(f"{k} = {v}" for k, v in cfg.items()), "small"))
    annex.append(
        _p(
            "Dados: contém dados Copernicus Sentinel modificados (ESA/UE); Copernicus DEM GLO-30.",
            "small",
        )
    )

    story.append(KeepTogether(annex))

    out.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.2 * cm,
        title=f"TerraVisão — {title}",
        author="TerraVisão",
    ).build(story, onFirstPage=_footer, onLaterPages=_footer)
    return out
