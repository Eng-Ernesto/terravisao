"""Auxiliares de mapa e de apresentação partilhados pelos módulos da interface."""

from __future__ import annotations

import html
from typing import Any

import folium
import streamlit as st
from shapely.geometry import shape

from . import data

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
