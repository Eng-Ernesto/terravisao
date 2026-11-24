"""Módulo «Análise de mapa» do GeoExplora IA: o geofísico carrega dados e a plataforma analisa."""

from __future__ import annotations

import hashlib
import html
import tempfile
from pathlib import Path
from typing import Any

import folium
import numpy as np
import streamlit as st
from streamlit_folium import st_folium

from geoexplora import demo, geophysics
from geoexplora.analysis import CLASS_LABEL, Analysis, Params
from geoexplora.analysis import run as run_analysis
from geoexplora.assistant import Assistant, brief
from geoexplora.loaders import LoadError, read_grid, read_points

from . import data, theme
from .maps import base_options, fmt_coord, label, new_map, top_bar

UPLOAD = "Carregar os meus dados"
CLASS_COLOR = {"baixa": theme.MOSS, "moderada": theme.OCHRE, "elevada": theme.OXIDE}
CRS_OPTIONS = {
    "Automático (graus ou UTM 33S)": None,
    "WGS 84 / UTM 32S (EPSG:32732)": 32732,
    "WGS 84 / UTM 33S (EPSG:32733)": 32733,
    "WGS 84 / UTM 34S (EPSG:32734)": 32734,
}
SUGGESTIONS = [
    "Resume o resultado",
    "Onde estão as zonas?",
    "Há relação com a geofísica?",
    "O modelo funciona?",
    "Qual o próximo passo?",
]
DERIVATIVES = {
    "valor": None,
    "sinal analítico": geophysics.analytic_signal,
    "1.ª derivada vertical": geophysics.vertical_derivative,
    "gradiente horizontal": geophysics.horizontal_gradient,
}


@st.cache_data(show_spinner="A analisar os dados…", max_entries=8)
def compute(
    folder: str,
    up_name: str,
    up_bytes: bytes,
    grid_files: tuple[tuple[str, bytes], ...],
    epsg: int | None,
    method: str,
    q_mod: float,
    q_elev: float,
) -> Analysis:
    params = Params(method=method, q_moderada=q_mod, q_elevada=q_elev)
    if folder:
        pts, grids, _ = demo.load(Path(folder))
    else:
        pts = read_points(up_bytes, up_name, epsg=epsg)
        pts.title = Path(up_name).stem
        grids = {Path(n).stem: read_grid(b, Path(n).stem) for n, b in grid_files}
    return run_analysis(pts, params, grids)


@st.cache_data(show_spinner="A gerar o relatório…", max_entries=4)
def report_bytes(*args: Any) -> bytes:
    from geoexplora.report import generate_analysis_report

    a = compute(*args)
    out = Path(tempfile.mkdtemp()) / "relatorio.pdf"
    return generate_analysis_report(a, out).read_bytes()


def _opts() -> dict[str, Any]:
    """Escolhas da barra lateral. Devolve tudo o que a página precisa."""
    datasets = demo.list_datasets()
    o: dict[str, Any] = {"folder": "", "up_name": "", "up_bytes": b"", "grids": (), "epsg": None}
    with st.sidebar:
        label("Dados")
        source = st.selectbox(
            "Dados", [*datasets, UPLOAD], key="geo_source", label_visibility="collapsed"
        )
        o["source"] = source
        if source == UPLOAD:
            f = st.file_uploader(
                "Amostras (CSV, GeoJSON ou Shapefile .zip)",
                type=["csv", "geojson", "json", "zip"],
                key="geo_up",
            )
            gs = st.file_uploader(
                "Grelhas geofísicas (GeoTIFF, opcional)",
                type=["tif", "tiff"],
                accept_multiple_files=True,
                key="geo_grids",
            )
            crs = st.selectbox("Coordenadas", list(CRS_OPTIONS), key="geo_crs")
            if f is not None:
                o["up_name"], o["up_bytes"] = f.name, f.getvalue()
            o["grids"] = tuple((g.name, g.getvalue()) for g in gs)
            o["epsg"] = CRS_OPTIONS[crs]
        else:
            o["folder"] = str(datasets[source])
        label("Classificação")
        method = st.radio(
            "Método",
            ["quantis", "estatistico"],
            format_func=lambda m: (
                "Quantis do conjunto" if m == "quantis" else "Desvios (média + 1σ, + 2σ)"
            ),
            label_visibility="collapsed",
        )
        o["method"] = method
        if method == "quantis":
            q_mod, q_elev = st.slider(
                "Moderada e elevada (percentis)", 0.30, 0.95, (0.50, 0.85), 0.05
            )
        else:
            q_mod, q_elev = 0.50, 0.85
        o["q_mod"], o["q_elev"] = float(q_mod), float(q_elev)
    return o


def _layers_sidebar(a: Analysis, sat: Path | None) -> dict[str, Any]:
    with st.sidebar:
        label("Camadas do mapa")
        out: dict[str, Any] = {
            "points": st.checkbox("Amostras por classe", value=True),
            "zones": st.checkbox("Zonas de interesse", value=True),
            "all_zones": st.checkbox("Incluir zonas não significativas", value=False),
            "surface": st.checkbox(f"Superfície ({a.treo_label.split(' (')[0]})", value=False),
            "sat": st.checkbox("Imagem de satélite (TerraVisão)", value=True, disabled=sat is None),
            "grid": "Nenhuma",
        }
        if a.grids:
            choices = ["Nenhuma"] + [f"{g} · {d}" for g in a.grids for d in DERIVATIVES]
            out["grid"] = st.selectbox("Grelha geofísica", choices)
        out["opacity"] = st.slider("Opacidade das camadas", 0.2, 1.0, 0.75, 0.05, key="geo_op")
        out["base"] = st.radio("Base do mapa", base_options(), key="geo_base")
    return out


def _grid_layer(
    a: Analysis, choice: str
) -> tuple[np.ndarray, tuple[float, float, float, float], str]:
    name, _, deriv = choice.partition(" · ")
    g = a.grids[name]
    arr = g.array
    fn = DERIVATIVES[deriv]
    if fn is not None:
        arr = fn(arr, g.resolution)
    x0, y0, x1, y1 = g.bounds()
    return arr, (x0, y0, x1, y1), choice


def _build_map(a: Analysis, lay: dict[str, Any], sat: Path | None) -> folium.Map:
    df = a.points.df
    centre = (float(df["lat"].mean()), float(df["lon"].mean()))
    m = new_map(centre[0], centre[1], 13, lay["base"])
    op = lay["opacity"]
    if lay["sat"] and sat is not None:
        uri, b = data.raster_overlay(sat, "layer_rgb", "rgb", 1.0)
        folium.raster_layers.ImageOverlay(uri, bounds=b, name="Satélite").add_to(m)
    if lay["grid"] != "Nenhuma":
        arr, (x0, y0, x1, y1), title = _grid_layer(a, lay["grid"])
        lo, hi = np.nanpercentile(arr, [2, 98])
        cmap = "RdBu_r" if lo < 0 < hi else "viridis"
        uri = data.array_png(arr, cmap, float(lo), float(hi), op)
        folium.raster_layers.ImageOverlay(
            uri,
            bounds=data.lonlat_bounds(x0, y0, x1, y1, a.grids[title.split(" · ")[0]].epsg),
            name=title,
        ).add_to(m)
    if lay["surface"]:
        s = a.surface
        rows, cols = s.array.shape
        lo, hi = np.nanpercentile(s.array, [2, 98])
        uri = data.array_png(s.array, "YlOrBr", float(lo), float(hi), op)
        b = data.lonlat_bounds(s.x0, s.y1 - rows * s.dx, s.x0 + cols * s.dx, s.y1, s.epsg)
        folium.raster_layers.ImageOverlay(uri, bounds=b, name="Superfície").add_to(m)
    if lay["zones"]:
        for z in a.zones:
            if not (z.significant or lay["all_zones"]):
                continue
            folium.GeoJson(
                {"type": "Feature", "geometry": z.polygon, "properties": {}},
                style_function=lambda _f, sig=z.significant: {
                    "color": theme.OXIDE if sig else "#6B675D",
                    "weight": 2.2 if sig else 1.2,
                    "dashArray": None if sig else "5 4",
                    "fillColor": theme.OXIDE,
                    "fillOpacity": 0.10 if sig else 0.0,
                },
                tooltip=(
                    f"Zona {z.id}: {z.n_samples} amostras elevadas, {z.area_km2:.1f} km², "
                    f"média {z.mean_value_ppm:.0f} ppm"
                    + ("" if z.significant else " (compatível com o acaso)")
                ),
            ).add_to(m)
    if lay["points"]:
        for r in df.itertuples():
            cls = str(r.classe)
            tip = f"{r.id}: {r.metrica_ppm:.0f} ppm · {CLASS_LABEL[cls]}"
            if hasattr(r, "ndpr_share"):
                tip += f" · NdPr {r.ndpr_share * 100:.0f} %"
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=6 if cls == "elevada" else 4,
                color=theme.INK,
                weight=0.9,
                fill=True,
                fill_color=CLASS_COLOR[cls],
                fill_opacity=0.95,
                tooltip=tip,
            ).add_to(m)
    m.fit_bounds([[df["lat"].min(), df["lon"].min()], [df["lat"].max(), df["lon"].max()]])
    return m


def _result_strip(a: Analysis) -> None:
    counts, total = a.class_counts, max(len(a.points.df), 1)
    bar = "".join(
        f'<span style="width:{counts[k] / total * 100:.1f}%;background:{CLASS_COLOR[k]}"></span>'
        for k in ("baixa", "moderada", "elevada")
    )
    legend = "".join(
        f'<span><span class="tv-dot" style="background:{CLASS_COLOR[k]}"></span> {CLASS_LABEL[k]} '
        f'<span class="tv-num">{counts[k]}</span></span>'
        for k in ("baixa", "moderada", "elevada")
    )
    th = a.thresholds
    left = (
        '<div class="tv-h">Classificação</div>'
        f'<div class="tv-meta">{html.escape(a.treo_label)}, {total} amostras</div>'
        f'<div class="tv-bar">{bar}</div><div class="tv-legend">{legend}</div>'
        f'<div class="tv-meta" style="margin-top:8px">Moderada ≥ <span class="tv-num">{th["moderada"]:.0f}</span> ppm · '
        f'Elevada ≥ <span class="tv-num">{th["elevada"]:.0f}</span> ppm</div>'
    )
    rows = ""
    for z in a.zones:
        sig = "sim" if z.significant else "não"
        ndpr = "—" if z.ndpr_share is None else f"{z.ndpr_share * 100:.0f} %"
        rows += (
            f'<tr><td><span class="tv-zid">{z.id}</span></td><td class="tv-num">{z.n_samples}</td>'
            f'<td class="tv-num">{z.area_km2:.1f} km²</td><td class="tv-num">{z.mean_value_ppm:.0f}</td>'
            f'<td class="tv-num">{ndpr}</td><td>{sig}</td></tr>'
        )
    table = (
        '<table class="tv-zones"><thead><tr><th>Zona</th><th>Amostras</th><th>Área</th>'
        "<th>Média (ppm)</th><th>NdPr/TREO</th><th>Maior que o acaso</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if rows
        else '<div class="tv-meta">Nenhuma zona de interesse.</div>'
    )
    m = a.model
    if m.get("executado"):
        verdict = (
            f'<span class="tv-pill" style="border-color:{theme.MOSS};color:{theme.MOSS}">supera o acaso</span>'
            if m["supera_acaso"]
            else f'<span class="tv-pill" style="border-color:{theme.OXIDE};color:{theme.OXIDE}">não supera o acaso</span>'
        )
        model_html = (
            f'<div class="tv-h" style="margin-top:14px">Modelo de apoio</div>{verdict}'
            f'<span class="tv-meta">exatidão {m["exatidao"] * 100:.0f} % · acaso {m["acaso"] * 100:.0f} %</span>'
        )
    else:
        model_html = ""
    rel = "".join(
        f'<div class="tv-meta"><span class="tv-num">{r["rho_spearman"]:+.2f}</span> '
        f"{html.escape(r['variavel'])} <i>({r['leitura']})</i></div>"
        for r in a.correlations[:4]
    )
    relations = (
        f'<div class="tv-h" style="margin-top:14px">Relação com a geofísica</div>{rel}'
        if rel
        else ""
    )
    st.markdown(
        f'<div class="tv-strip"><div>{left}{relations}{model_html}</div>'
        f'<div><div class="tv-h">Zonas de interesse</div><div class="tv-scroll">{table}</div>'
        '<div class="tv-note">Classes relativas ao conjunto, não são teores económicos. '
        "Confirme sempre no campo.</div></div></div>",
        unsafe_allow_html=True,
    )


def _chat(a: Analysis, key: str) -> None:
    with st.sidebar, st.expander("Assistente de IA (opcional)"):
        st.caption(
            "Sem token, o assistente responde offline. Com a conta Cloudflare Workers AI "
            "(gratuita), responde em linguagem livre. Os dados do resumo são enviados à Cloudflare."
        )
        st.text_input("Account ID", key="cf_account", type="password")
        st.text_input("Token da API", key="cf_token", type="password")
    assistant = Assistant(
        a.summary(),
        account_id=st.session_state.get("cf_account") or None,
        token=st.session_state.get("cf_token") or None,
    )
    history = st.session_state.setdefault(f"chat::{key}", [])
    if not history:
        history.append({"role": "assistant", "content": brief(a.summary()), "origin": "offline"})

    st.markdown('<div class="tv-h">Assistente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tv-sub">'
        + (
            "Com IA (Cloudflare Workers AI)"
            if assistant.mode == "ia"
            else "Modo offline: respostas automáticas"
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    box = st.container(height=380)
    pending: str | None = None
    for i, text in enumerate(SUGGESTIONS):
        if st.button(text, key=f"sug-{key}-{i}", use_container_width=True):
            pending = text
    typed = st.chat_input("Pergunte sobre os resultados…", key=f"in-{key}")
    question = typed or pending
    if question:
        past = [{"role": m["role"], "content": m["content"]} for m in history[1:]]
        history.append({"role": "user", "content": question, "origin": ""})
        answer, origin = assistant.ask(question, past)
        history.append({"role": "assistant", "content": answer, "origin": origin})
    # Troca mais recente (pergunta + resposta) no topo: a resposta fica sempre visível.
    exchanges = [history[i : i + 2] for i in range(1, len(history), 2)]
    with box:
        for group in [*reversed(exchanges), history[:1]]:
            for msg in group:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and msg["origin"] == "ia":
                        st.caption("resposta da IA, com base nos resultados")


def render() -> None:
    o = _opts()
    if o["source"] == UPLOAD and not o["up_bytes"]:
        top_bar("Análise de mapa", "Carregue os seus dados", "")
        st.info(
            "Carregue um CSV, GeoJSON ou Shapefile (zip) com amostras. Precisa de coordenadas "
            "(X e Y em UTM, ou lon e lat) e colunas de elementos como Ce_ppm, La_ppm, Nd_ppm, Pr_ppm "
            "(terras raras) ou Cu_ppm, Li_ppm (outros minerais críticos). Pode juntar grelhas "
            "geofísicas em GeoTIFF (por exemplo, anomalia magnética)."
        )
        return
    args = (
        o["folder"],
        o["up_name"],
        o["up_bytes"],
        o["grids"],
        o["epsg"],
        o["method"],
        o["q_mod"],
        o["q_elev"],
    )
    try:
        a = compute(*args)
    except (LoadError, ValueError) as exc:
        top_bar("Análise de mapa", "Erro nos dados", "")
        st.error(str(exc))
        return

    df = a.points.df
    sat = data.find_satellite_base(df["lon"].to_numpy(), df["lat"].to_numpy())
    lay = _layers_sidebar(a, sat)
    key = hashlib.md5(repr(args[:4]).encode()).hexdigest()[:10]

    with st.sidebar:
        label("Exportar")
        st.download_button(
            "Relatório técnico (PDF)",
            data=report_bytes(*args),
            file_name="geoexplora_relatorio.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        csv = df.drop(columns=["x", "y"]).to_csv(index=False).encode("utf-8")
        st.download_button(
            "Amostras classificadas (CSV)",
            csv,
            "amostras_classificadas.csv",
            "text/csv",
            use_container_width=True,
        )
        st.markdown(
            '<div class="tv-foot">Ferramenta de apoio à interpretação. Indica onde vale a pena '
            "confirmar no campo; não confirma mineralização.</div>",
            unsafe_allow_html=True,
        )

    top_bar(
        a.points.title or "Análise de mapa",
        "Análise de mapa · " + a.treo_label,
        fmt_coord(float(df["lat"].mean()), float(df["lon"].mean())),
    )
    if a.points.fictitious:
        st.markdown(
            '<span class="tv-badge">Dados fictícios · demonstração</span>', unsafe_allow_html=True
        )
    for w in dict.fromkeys(a.warnings):
        st.caption("Aviso: " + w)

    map_col, chat_col = st.columns([2.3, 1], gap="large")
    with map_col:
        st_folium(
            _build_map(a, lay, sat), use_container_width=True, height=470, returned_objects=[]
        )
        _result_strip(a)
    with chat_col:
        _chat(a, key)
