"""Tema visual (docs/12-design-ui.md): papel, tinta e um único acento óxido."""

PAPER = "#F4F1EA"
PAPER_DARK = "#EAE5D9"
INK = "#1C1B18"
INK_SOFT = "#6B675D"
LINE = "#D8D2C4"
OXIDE = "#B4532A"
OCHRE = "#C9A227"
MOSS = "#5E7A63"
BASALT = "#2B2F33"

LEVEL_COLOR = {"baixa": MOSS, "media": OCHRE, "alta": OXIDE}
LEVEL_LABEL = {"baixa": "Baixa", "media": "Média", "alta": "Alta"}
TARGET_LABEL = {"ferro": "Ferro", "cobre": "Cobre", "ouro": "Ouro", "agua": "Água subterrânea"}

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
  --paper:{PAPER}; --paper-dark:{PAPER_DARK}; --ink:{INK}; --ink-soft:{INK_SOFT};
  --line:{LINE}; --oxide:{OXIDE}; --ochre:{OCHRE}; --moss:{MOSS}; --basalt:{BASALT};
}}
html, body, [class*="css"], .stApp {{
  font-family: 'Inter', system-ui, 'Segoe UI', sans-serif; color: var(--ink);
}}
.stApp {{ background: var(--paper); }}

/* Esconde a moldura do Streamlit */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stHeader"],
[data-testid="stDecoration"], [data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

.block-container {{ padding: 0 1.75rem 1.25rem 1.75rem !important; max-width: none !important; }}

/* Barra superior */
.tv-top {{
  display:flex; align-items:baseline; justify-content:space-between;
  padding: 18px 0 14px 0; border-bottom: 1px solid var(--line); margin-bottom: 14px;
}}
.tv-brand {{ font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:22px; letter-spacing:-0.01em; }}
.tv-place {{ color:var(--ink-soft); margin-left:14px; font-size:14px; }}
.tv-coords {{ font-family:'IBM Plex Mono', monospace; font-size:12px; color:var(--ink-soft); }}

/* Painel lateral */
[data-testid="stSidebar"] {{ background: var(--paper-dark); border-right: 1px solid var(--line); min-width:290px; max-width:290px; }}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 8px; }}
.tv-side-title {{ font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:20px; margin: 6px 0 2px 0; }}
.tv-side-sub {{ color:var(--ink-soft); font-size:12.5px; margin-bottom:18px; }}
.tv-label {{ font-size:11px; letter-spacing:.09em; text-transform:uppercase; color:var(--ink-soft); margin: 18px 0 6px 0; font-weight:600; }}
.tv-foot {{ color:var(--ink-soft); font-size:11.5px; line-height:1.45; border-top:1px solid var(--line); padding-top:12px; margin-top:24px; }}

/* Controlos nativos mais discretos */
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{ font-size:14px; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: var(--paper); border-color: var(--line); border-radius: 4px; }}
div[role="radiogroup"] label {{ padding: 2px 0; }}

/* Mapa */
iframe[title="streamlit_folium.st_folium"] {{ height: clamp(420px, calc(100vh - 300px), 760px) !important; border:1px solid var(--line); border-radius:4px; }}

/* Faixa de resultado */
.tv-strip {{ display:grid; grid-template-columns: 300px minmax(0,1fr); gap: 28px; margin-top: 16px; }}
.tv-scroll {{ overflow-x:auto; }}
@media (max-width: 1100px) {{ .tv-strip {{ grid-template-columns: 1fr; gap: 20px; }} }}
.tv-h {{ font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:18px; margin:0 0 8px 0; }}
.tv-chip {{ display:inline-flex; align-items:center; gap:8px; font-weight:600; font-size:15px; }}
.tv-dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
.tv-meta {{ color:var(--ink-soft); font-size:13px; margin-top:4px; }}
.tv-bar {{ display:flex; height:6px; margin:14px 0 6px 0; background:var(--line); border-radius:3px; overflow:hidden; }}
.tv-bar span {{ display:block; height:100%; }}
.tv-legend {{ font-size:12px; color:var(--ink-soft); display:flex; gap:14px; flex-wrap:wrap; }}
.tv-num {{ font-family:'IBM Plex Mono', monospace; font-size:12.5px; }}

table.tv-zones {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
table.tv-zones th {{ text-align:left; font-weight:500; font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); border-bottom:1px solid var(--line); padding:6px 10px 6px 0; }}
table.tv-zones td {{ border-bottom:1px solid var(--line); padding:9px 10px 9px 0; vertical-align:top; }}
.tv-zid {{ font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:16px; color:var(--oxide); }}
.tv-contrib {{ display:flex; flex-direction:column; gap:3px; min-width:160px; }}
.tv-contrib div {{ display:flex; align-items:center; gap:6px; font-size:11.5px; color:var(--ink-soft); }}
.tv-contrib i {{ display:block; height:4px; background:var(--ink); opacity:.75; border-radius:2px; }}
.tv-status {{ display:flex; align-items:center; gap:10px; font-size:13.5px; margin:0 0 10px 0; min-height:22px; }}
.tv-status .tv-num {{ color:var(--ink-soft); }}
.tv-hint {{ color:var(--ink-soft); font-size:12.5px; line-height:1.5; margin:6px 0 10px 0; }}
.stButton > button[kind="primary"] {{ background:var(--oxide); border:1px solid var(--oxide); color:#fff; border-radius:4px; font-weight:600; width:100%; }}
.stButton > button[kind="primary"]:disabled {{ background:var(--line); border-color:var(--line); color:var(--ink-soft); }}
.tv-note {{ color:var(--ink-soft); font-size:12px; margin-top:12px; }}
"""
