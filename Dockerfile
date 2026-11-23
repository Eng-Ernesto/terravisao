FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AWS_NO_SIGN_REQUEST=YES

WORKDIR /srv

# Camada de dependências primeiro, para aproveitar a cache do Docker.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[geo,app,report]"

COPY app ./app
COPY data/reference ./data/reference
COPY data/demo ./data/demo

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
