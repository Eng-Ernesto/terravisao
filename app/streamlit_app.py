"""Interface Streamlit (esqueleto). A lógica científica vive em `terravisao`, nunca aqui."""

import streamlit as st

from terravisao import __version__

st.set_page_config(page_title="TerraVisão", layout="wide")
st.title("TerraVisão")
st.caption(f"Plataforma de prospecção inteligente · v{__version__}")
st.info(
    "Ferramenta de triagem. Não confirma a existência de minerais ou água "
    "e não substitui o trabalho de campo."
)
st.write("Em desenvolvimento: desenho do terreno, análise e resultados (fase 2).")
