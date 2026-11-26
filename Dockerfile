# GeoExplora IA: frontend React (compilado com Node) servido pela API FastAPI.

# ---- 1. Frontend ---------------------------------------------------------------
FROM node:22-slim AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. API + análise -------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     AWS_NO_SIGN_REQUEST=YES     TERRAVISAO_CACHE_DIR=/srv/data/cache     GEOEXPLORA_ROOT=/srv

WORKDIR /srv

# Camada de dependências primeiro, para aproveitar a cache do Docker.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[geo,analysis,report,web]"

# Fronteiras de Angola, exemplos e resultados de demonstração (funcionam sem internet).
COPY data/reference ./data/reference
COPY data/samples ./data/samples
COPY data/demo ./data/demo
COPY data/geoexplora ./data/geoexplora
# Frontend compilado na fase 1.
COPY --from=frontend /web/dist ./frontend/dist

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s   CMD python -c "import os,urllib.request as u; u.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8501)}/api/health')"
# Forma shell (não exec) para expandir $PORT: hospedagens como o Render injectam essa
# variável e esperam que a app escute nela; localmente (Docker Compose) cai em 8501.
CMD python -m geoexplora.web --host 0.0.0.0 --port ${PORT:-8501}
