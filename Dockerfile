FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AWS_NO_SIGN_REQUEST=YES \
    TERRAVISAO_CACHE_DIR=/srv/data/cache

WORKDIR /srv

# Camada de dependências primeiro, para aproveitar a cache do Docker.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[geo,app,report]"

# Tema e activos locais (fontes, Leaflet): a app funciona sem internet.
COPY .streamlit ./.streamlit
COPY app ./app
# Fronteiras de Angola, regras e exemplos de terrenos.
COPY data/reference ./data/reference
COPY data/samples ./data/samples
# Resultados de demonstração pré-calculados (Longonjo, Lubango).
COPY data/demo ./data/demo

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
