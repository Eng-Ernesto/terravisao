"""TerraVisão — interface Streamlit. Só apresenta e orquestra; a ciência vive em `terravisao`."""

from __future__ import annotations

import html
import io
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import folium
import streamlit as st
from folium.plugins import Draw
from shapely.geometry import shape
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent))

from terravisao.aoi import AoiError, area_km2, validate_aoi  # noqa: E402
from terravisao.config import Target  # noqa: E402
from ui import data, theme  # noqa: E402

st.set_page_config(page_title="TerraVisão", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{theme.CSS}</style>", unsafe_allow_html=True)

LAYERS = {
    "classe": ("Classe de probabilidade", "class", "class_{t}"),
    "pontuacao": ("Pontuação", "score", "score_{t}"),
    "oxido": ("Óxido de ferro", "index", "layer_iron_oxide"),
    "argila": ("Alteração argilosa", "index", "layer_clay"),
    "relevo": ("Relevo (sombreado)", "relief", "layer_hillshade"),
    "rgb": ("Imagem de satélite", "rgb", "layer_rgb"),
}
LAYER_NAMES = {
    "iron_oxide": "Óxido de ferro",
    "clay": "Argila",
    "ferrous": "Ferroso",
    "lineament_density": "Lineamentos",
    "slope_inv": "Declive baixo",
    "twi": "Humidade do terreno",
    "drainage_density_inv": "Drenagem esparsa",
    "ndvi": "Vegetação",
    "lithology": "Litologia",
}
PLACES = {
    "Angola (vista geral)": (-12.5, 17.5, 6),
    "Longonjo, Huambo": (-12.92, 15.27, 12),
    "Huambo": (-12.78, 15.74, 11),
    "Lubango, Huíla": (-14.92, 13.49, 11),
    "Benguela": (-12.58, 13.41, 11),
    "Luanda": (-8.84, 13.23, 10),
}
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
FILL_MAP_CSS = (
    "<style>html,body,.float-child{height:100%;margin:0}"
    ".leaflet-container{position:absolute!important;inset:0;height:100%!important;width:100%!important;"
    "background:#EAE5D9!important}</style>"
)
# Leaflet servido localmente (app/static): o mapa funciona sem internet.
STATIC = "/app/static/leaflet"
LOCAL_JS = [("leaflet", f"{STATIC}/leaflet.js")]
LOCAL_CSS = [("leaflet_css", f"{STATIC}/leaflet.css")]
BASE_OFFLINE = "Offline"
BASE_SAT = "Online: satélite"
BASE_LIGHT = "Online: mapa claro"


@st.cache_data(show_spinner="A gerar o relatório…")
def report_pdf(folder: str) -> bytes:
    from terravisao.report import generate_report

    out = Path(tempfile.mkdtemp()) / "relatorio.pdf"
    return generate_report(Path(folder), out).read_bytes()


@st.cache_data(show_spinner=False)
def data_zip(folder: str) -> bytes:
    """Pontuação, classes e zonas de cada alvo, camadas e run.json (RF-22)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(Path(folder).iterdir()):
            if f.suffix in {".tif", ".geojson", ".json"}:
                zf.write(f, f.name)
    return buf.getvalue()


def label(text: str) -> None:
    st.markdown(f'<div class="tv-label">{text}</div>', unsafe_allow_html=True)


def fmt_coord(lat: float, lon: float) -> str:
    ns, ew = ("S" if lat < 0 else "N"), ("W" if lon < 0 else "E")
    return f"{abs(lat):.2f}°{ns}  {abs(lon):.2f}°{ew}".replace(".", ",")


def outlines(geometry: dict[str, Any]) -> list[list[list[float]]]:
    geom = shape(geometry)
    polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    return [[[y, x] for x, y in p.exterior.coords] for p in polys]


def base_options() -> list[str]:
    """Offline sempre; bases online só quando há internet."""
    return [BASE_OFFLINE, BASE_SAT, BASE_LIGHT] if data.is_online() else [BASE_OFFLINE]


def new_map(lat: float, lon: float, zoom: int, base: str) -> folium.Map:
    online = base in (BASE_SAT, BASE_LIGHT)
    tiles = ESRI.format("World_Imagery" if base == BASE_SAT else "Canvas/World_Light_Gray_Base")
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=tiles if online else None,
        attr="Esri, HERE, Garmin, Maxar" if online else None,
        zoom_control=True,
        control_scale=True,
        max_zoom=16,
    )
    m.default_js, m.default_css = LOCAL_JS, LOCAL_CSS
    # O folium usa uma caixa com proporção fixa; forçar o mapa a preencher o quadro.
    m.get_root().header.add_child(folium.Element(FILL_MAP_CSS))
    if not online:  # base offline: fronteiras das províncias (domínio público)
        folium.GeoJson(
            data.provinces(),
            style_function=lambda _f: {"color": "#B9B2A0", "weight": 1, "fillOpacity": 0},
            tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["Província"]),
        ).add_to(m)
    return m


def top_bar(title: str, place: str, coords: str) -> None:
    st.markdown(
        f'<div class="tv-top"><div><span class="tv-brand">{html.escape(title)}</span>'
        f'<span class="tv-place">{html.escape(place)}</span></div>'
        f'<div class="tv-coords">{coords}</div></div>',
        unsafe_allow_html=True,
    )


def sidebar_header() -> str:
    with st.sidebar:
        st.markdown('<div class="tv-side-title">TerraVisão</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="tv-side-sub">Triagem de potencial mineral e hídrico</div>',
            unsafe_allow_html=True,
        )
        mode = st.radio(
            "Modo", ["Resultados", "Nova análise"], key="mode", label_visibility="collapsed"
        )
    return str(mode)


def sidebar_footer() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="tv-foot">Ferramenta de triagem. Indica onde vale a pena confirmar no '
            "campo; não confirma a existência de minerais ou de água.</div>",
            unsafe_allow_html=True,
        )


# ====================================================================== Resultados
def results_view() -> None:
    demos = data.list_demos()
    if not demos:
        st.info("Ainda não há resultados. Use «Nova análise» para analisar um terreno.")
        sidebar_footer()
        return

    with st.sidebar:
        label("Terreno")
        site = st.selectbox("Terreno", list(demos), key="site", label_visibility="collapsed")
        folder = demos[site]
        run = data.load_run(folder)
        targets = list(run["summary"]["targets"])
        if not targets:
            st.warning("Esta análise não produziu resultados.")
            return
        label("Alvo")
        target = st.radio(
            "Alvo",
            targets,
            format_func=lambda t: theme.TARGET_LABEL[t],
            label_visibility="collapsed",
        )
        label("Camada")
        layer_key = st.radio(
            "Camada",
            list(LAYERS),
            format_func=lambda k: LAYERS[k][0],
            label_visibility="collapsed",
        )
        show_zones = st.checkbox("Contornos das zonas", value=True)
        opacity = st.slider("Opacidade", 0.2, 1.0, 0.75, 0.05)
        underlay = st.checkbox(
            "Imagem de satélite por baixo",
            value=True,
            disabled=not data.has_layer(folder, "layer_rgb"),
        )
        basemap = st.radio("Base do mapa", base_options())
        label("Exportar")
        st.download_button(
            "Relatório (PDF)",
            data=report_pdf(str(folder)),
            file_name=f"terravisao_{folder.name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.download_button(
            "Dados (GeoTIFF e GeoJSON)",
            data=data_zip(str(folder)),
            file_name=f"terravisao_{folder.name}_dados.zip",
            mime="application/zip",
            use_container_width=True,
        )
    sidebar_footer()

    res = run["summary"]["targets"][target]
    geometry = run["request"]["geometry"]
    centre = shape(geometry).centroid
    lat, lon = centre.y, centre.x
    top_bar(
        site,
        f"{run['meta'].get('region', '')} · {theme.TARGET_LABEL[target]}",
        fmt_coord(lat, lon),
    )

    m = new_map(lat, lon, 13, basemap)
    title, kind, pattern = LAYERS[layer_key]
    if underlay and kind != "rgb" and data.has_layer(folder, "layer_rgb"):
        base_uri, base_bounds = data.raster_overlay(folder, "layer_rgb", "rgb", 1.0)
        folium.raster_layers.ImageOverlay(base_uri, bounds=base_bounds, name="Satélite").add_to(m)
    uri, bounds = data.raster_overlay(folder, pattern.format(t=target), kind, opacity)
    folium.raster_layers.ImageOverlay(uri, bounds=bounds, opacity=1.0, name=title).add_to(m)
    for ring in outlines(geometry):
        folium.PolyLine(ring, color=theme.INK, weight=1.2, dash_array="5 5", opacity=0.8).add_to(m)
    if show_zones:
        folium.GeoJson(
            data.load_zones(folder, target),
            style_function=lambda _f: {"color": theme.OXIDE, "weight": 2, "fillOpacity": 0.0},
            tooltip=folium.GeoJsonTooltip(
                fields=["id", "area_km2"], aliases=["Zona", "Área (km²)"]
            ),
        ).add_to(m)
    m.fit_bounds(bounds)
    st_folium(m, use_container_width=True, height=520, returned_objects=[])

    result_strip(run, folder, target, res)


def result_strip(run: dict[str, Any], folder: Path, target: str, res: dict[str, Any]) -> None:
    level, conf, areas = res["classe_final"], res["confianca"], res["area_por_classe_km2"]
    total = sum(areas.values()) or 1.0
    bar = "".join(
        f'<span style="width:{areas[k] / total * 100:.1f}%;background:{theme.LEVEL_COLOR[k]}"></span>'
        for k in ("baixa", "media", "alta")
    )
    legend = "".join(
        f'<span><span class="tv-dot" style="background:{theme.LEVEL_COLOR[k]}"></span> '
        f'{theme.LEVEL_LABEL[k]} <span class="tv-num">{areas[k]:.1f} km²</span></span>'
        for k in ("baixa", "media", "alta")
    )
    left = (
        '<div class="tv-h">Resultado</div>'
        f'<div class="tv-chip"><span class="tv-dot" style="background:{theme.LEVEL_COLOR[level]}"></span>'
        f"Probabilidade {theme.LEVEL_LABEL[level].lower()}</div>"
        f'<div class="tv-meta">Confiança dos dados: {theme.LEVEL_LABEL[conf].lower()}</div>'
        f'<div class="tv-bar">{bar}</div><div class="tv-legend">{legend}</div>'
    )
    zones = {
        f["properties"]["id"]: f["properties"] for f in data.load_zones(folder, target)["features"]
    }
    rows = ""
    for z in res["zonas"]:
        p = zones.get(z["id"], {})
        top = sorted(p.get("contributions", {}).items(), key=lambda kv: kv[1], reverse=True)[:3]
        mx = max((v for _, v in top), default=1) or 1
        bars = "".join(
            f'<div><i style="width:{v / mx * 70:.0f}px"></i>{LAYER_NAMES.get(k, k)}</div>'
            for k, v in top
        )
        rows += (
            f'<tr><td><span class="tv-zid">{html.escape(z["id"])}</span></td>'
            f'<td class="tv-num">{z["area_km2"] * 100:.1f} ha</td>'
            f'<td class="tv-num">{z["score_medio"]:.2f}</td>'
            f'<td><div class="tv-contrib">{bars}</div></td>'
            f"<td>{html.escape(p.get('recommendation', ''))}</td></tr>"
        )
    table = (
        '<table class="tv-zones"><thead><tr><th>Zona</th><th>Área</th><th>Pontuação</th>'
        "<th>Principais camadas</th><th>Método de campo sugerido</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if rows
        else '<div class="tv-meta">Nenhuma zona acima da área mínima (5 ha).</div>'
    )
    right = f'<div class="tv-h">Zonas prioritárias</div><div class="tv-scroll">{table}</div>'
    warn = run["summary"].get("warnings", [])
    note = (
        '<div class="tv-note">Pontuação relativa à área analisada. '
        + ("Sem mapa geológico: confiança limitada. " if any("Geologia" in w for w in warn) else "")
        + "Confirme sempre no campo.</div>"
    )
    st.markdown(
        f'<div class="tv-strip"><div>{left}</div><div>{right}{note}</div></div>',
        unsafe_allow_html=True,
    )


# ==================================================================== Nova análise
def geometry_from_upload(upload: Any) -> dict[str, Any] | None:
    if upload is None:
        return None
    try:
        gj = json.loads(upload.getvalue().decode("utf-8"))
        if gj.get("type") == "FeatureCollection":
            gj = gj["features"][0]
        return dict(gj["geometry"] if gj.get("type") == "Feature" else gj)
    except Exception:
        return None


def last_drawn(drawn: dict[str, Any] | None) -> dict[str, Any] | None:
    for feat in reversed((drawn or {}).get("all_drawings") or []):
        geom = feat.get("geometry")
        if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
            return dict(geom)
    return None


def status_line(kind: str, text: str, extra: str = "") -> None:
    color = {"ok": theme.MOSS, "error": theme.OXIDE, "idle": theme.LINE}[kind]
    st.markdown(
        f'<div class="tv-status"><span class="tv-dot" style="background:{color}"></span>'
        f'<span>{html.escape(text)}</span><span class="tv-num">{html.escape(extra)}</span></div>',
        unsafe_allow_html=True,
    )


def new_analysis_view() -> None:
    with st.sidebar:
        label("Nome do terreno")
        name = st.text_input("Nome", value="Meu terreno", label_visibility="collapsed")
        label("Ir para")
        place = st.selectbox("Local", list(PLACES), label_visibility="collapsed")
        label("Alvos")
        chosen = [
            t.value
            for t in Target
            if st.checkbox(theme.TARGET_LABEL[t.value], value=True, key=f"t_{t.value}")
        ]
        label("Ou carregue o terreno")
        upload = st.file_uploader("GeoJSON", type=["geojson", "json"], label_visibility="collapsed")
        basemap = st.radio("Base do mapa", base_options())
    sidebar_footer()

    lat, lon, zoom = PLACES[place]
    top_bar("Nova análise", "Desenhe o terreno no mapa", fmt_coord(lat, lon))

    uploaded = geometry_from_upload(upload)
    m = new_map(lat, lon, zoom, basemap)
    draw = Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "circle": False,
            "marker": False,
            "circlemarker": False,
            "polygon": {"allowIntersection": False, "shapeOptions": {"color": theme.OXIDE}},
            "rectangle": {"shapeOptions": {"color": theme.OXIDE}},
        },
        edit_options={"edit": True, "remove": True},
    )
    draw.default_js = [("leaflet_draw_js", f"{STATIC}/leaflet.draw.js")]
    draw.default_css = [("leaflet_draw_css", f"{STATIC}/leaflet.draw.css")]
    draw.add_to(m)
    if uploaded:
        for ring in outlines(uploaded):
            folium.Polygon(ring, color=theme.OXIDE, weight=2, fill_opacity=0.1).add_to(m)
    drawn = st_folium(
        m,
        use_container_width=True,
        height=520,
        key=f"draw-{place}-{basemap}",
        returned_objects=["all_drawings"],
    )

    geometry = uploaded or last_drawn(drawn)
    valid, error, area = False, "", 0.0
    if geometry is None:
        status_line("idle", "Use as ferramentas à esquerda do mapa para desenhar o terreno.")
    else:
        try:
            area = area_km2(validate_aoi(geometry))
            valid = True
            status_line("ok", "Terreno válido", f"{area:,.1f} km²".replace(",", " "))
        except AoiError as exc:
            error = str(exc)
            status_line("error", error)

    with st.sidebar:
        hint = (
            "A análise descarrega imagens de satélite e demora cerca de 1 a 3 minutos."
            if data.is_online()
            else "Sem internet: não é possível descarregar imagens de satélite, por isso só "
            "terrenos já analisados antes funcionam. Os exemplos continuam em «Resultados»."
        )
        st.markdown(f'<div class="tv-hint">{hint}</div>', unsafe_allow_html=True)
        go = st.button(
            "Analisar terreno", type="primary", disabled=not (valid and chosen), key="go"
        )
    if go and geometry is not None:
        analyse(geometry, name, chosen)


def analyse(geometry: dict[str, Any], name: str, chosen: list[str]) -> None:
    # Importação tardia: o pipeline carrega bibliotecas pesadas.
    from terravisao.export import export_all
    from terravisao.models import AnalysisRequest
    from terravisao.pipeline import run as run_pipeline

    progress = st.progress(0.0, text="A preparar…")
    request = AnalysisRequest(
        geometry=geometry, targets=[Target(t) for t in chosen], name=name.strip() or "terreno"
    )
    try:
        result = run_pipeline(request, progress=lambda m, f: progress.progress(f, text=m))
    except Exception as exc:
        progress.empty()
        st.error(f"A análise falhou: {exc}")
        return
    progress.empty()
    if not result.targets:
        st.error("Não foi possível obter dados para este terreno. " + " ".join(result.warnings))
        return

    stamp = datetime.now()
    slug = re.sub(r"[^a-z0-9]+", "-", request.name.lower()).strip("-") or "terreno"
    folder = data.RUNS_DIR / f"{slug}-{stamp:%Y%m%d-%H%M%S}"
    export_all(result, folder)
    title = f"{request.name} · {stamp:%d/%m %H:%M}"
    (folder / "meta.json").write_text(
        json.dumps({"title": title, "region": "Análise nova"}, ensure_ascii=False), encoding="utf-8"
    )
    st.session_state["_goto"] = title
    st.rerun()


# ============================================================================ Entrada
if "_goto" in st.session_state:  # definido por analyse(); aplicado antes de criar os widgets
    st.session_state["mode"] = "Resultados"
    st.session_state["site"] = st.session_state.pop("_goto")

if sidebar_header() == "Nova análise":
    new_analysis_view()
else:
    results_view()
