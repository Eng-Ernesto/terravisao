"""TerraVisão — interface Streamlit. Só apresenta resultados; a ciência vive em `terravisao`."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui import data, theme  # noqa: E402

st.set_page_config(page_title="TerraVisão", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{theme.CSS}</style>", unsafe_allow_html=True)

LAYERS = {
    "classe": ("Classe de probabilidade", "class", "class_{t}"),
    "pontuacao": ("Pontuação", "score", "score_{t}"),
    "oxido": ("Óxido de ferro", "index", "layer_iron_oxide"),
    "argila": ("Alteração argilosa", "index", "layer_clay"),
    "relevo": ("Relevo (sombreado)", "relief", "layer_hillshade"),
}


def fmt_coord(lat: float, lon: float) -> str:
    ns, ew = ("S" if lat < 0 else "N"), ("W" if lon < 0 else "E")
    return f"{abs(lat):.2f}°{ns}  {abs(lon):.2f}°{ew}".replace(".", ",")


def centroid(geometry: dict) -> tuple[float, float]:
    ring = geometry["coordinates"][0]
    return (sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring))


demos = data.list_demos()
if not demos:
    st.error("Sem dados de demonstração em data/demo/.")
    st.stop()

# ---------- Painel lateral ----------
with st.sidebar:
    st.markdown('<div class="tv-side-title">TerraVisão</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tv-side-sub">Triagem de potencial mineral e hídrico</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tv-label">Terreno</div>', unsafe_allow_html=True)
    site = st.selectbox("Terreno", list(demos), label_visibility="collapsed")
    folder = demos[site]
    run = data.load_run(folder)
    targets = list(run["summary"]["targets"])

    st.markdown('<div class="tv-label">Alvo</div>', unsafe_allow_html=True)
    target = st.radio(
        "Alvo", targets, format_func=lambda t: theme.TARGET_LABEL[t], label_visibility="collapsed"
    )

    st.markdown('<div class="tv-label">Camada</div>', unsafe_allow_html=True)
    layer_key = st.radio(
        "Camada", list(LAYERS), format_func=lambda k: LAYERS[k][0], label_visibility="collapsed"
    )
    show_zones = st.checkbox("Contornos das zonas", value=True)
    opacity = st.slider("Opacidade", 0.2, 1.0, 0.75, 0.05)
    basemap = st.radio("Base", ["Mapa claro", "Satélite"], horizontal=True)

    st.markdown(
        '<div class="tv-foot">Ferramenta de triagem. Indica onde vale a pena confirmar no campo; '
        "não confirma a existência de minerais ou de água.</div>",
        unsafe_allow_html=True,
    )

res = run["summary"]["targets"][target]
geometry = run["request"]["geometry"]
lat, lon = centroid(geometry)

# ---------- Barra superior ----------
region = run["meta"].get("region", "")
st.markdown(
    f'<div class="tv-top"><div><span class="tv-brand">{html.escape(site)}</span>'
    f'<span class="tv-place">{html.escape(region)} · {html.escape(theme.TARGET_LABEL[target])}</span></div>'
    f'<div class="tv-coords">{fmt_coord(lat, lon)}</div></div>',
    unsafe_allow_html=True,
)

# ---------- Mapa ----------
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
tiles = ESRI.format("World_Imagery" if basemap == "Satélite" else "Canvas/World_Light_Gray_Base")
m = folium.Map(
    location=[lat, lon],
    zoom_start=13,
    tiles=tiles,
    attr="Esri, HERE, Garmin, Maxar",
    zoom_control=True,
    control_scale=True,
    max_zoom=16,
)
title, kind, pattern = LAYERS[layer_key]
uri, bounds = data.raster_overlay(folder, pattern.format(t=target), kind, opacity)
folium.raster_layers.ImageOverlay(uri, bounds=bounds, opacity=1.0, name=title).add_to(m)
ring = [[p[1], p[0]] for p in geometry["coordinates"][0]]
folium.PolyLine(ring, color=theme.INK, weight=1.2, dash_array="5 5", opacity=0.8).add_to(m)
if show_zones:
    folium.GeoJson(
        data.load_zones(folder, target),
        style_function=lambda _f: {"color": theme.OXIDE, "weight": 2, "fillOpacity": 0.0},
        tooltip=folium.GeoJsonTooltip(fields=["id", "area_km2"], aliases=["Zona", "Área (km²)"]),
    ).add_to(m)
m.fit_bounds(bounds)
# O folium usa uma caixa com proporção fixa; forçar o mapa a preencher o quadro.
m.get_root().header.add_child(
    folium.Element(
        "<style>html,body,.float-child{height:100%;margin:0}.leaflet-container{position:absolute!important;inset:0;height:100%!important;width:100%!important}</style>"
    )
)
st_folium(m, use_container_width=True, height=520, returned_objects=[])

# ---------- Faixa de resultado ----------
level = res["classe_final"]
conf = res["confianca"]
areas = res["area_por_classe_km2"]
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
    f'<div class="tv-h">Resultado</div>'
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
    contrib = p.get("contributions", {})
    top = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)[:3]
    mx = max((v for _, v in top), default=1) or 1
    names = {
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
    bars = "".join(
        f'<div><i style="width:{v / mx * 70:.0f}px"></i>{names.get(k, k)}</div>' for k, v in top
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
    f'<div class="tv-strip"><div>{left}</div><div>{right}{note}</div></div>', unsafe_allow_html=True
)
