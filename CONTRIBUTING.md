# Contribuir

## Preparar o ambiente

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

Extras opcionais: `.[geo]` (raster/STAC), `.[app]` (Streamlit/pydeck), `.[report]` (PDF).

## Regras de arquitectura

1. **Lógica científica só em `src/terravisao/`.** A pasta `app/` apenas orquestra e mostra; não calcula.
2. **Funções puras** nos módulos de cálculo: entram arrays e parâmetros, saem arrays. Sem estado global.
3. **Pesos, limiares e bandas** só em `config.py` (e gravados na proveniência de cada resultado).
4. **Falha parcial não derruba a análise:** fontes devolvem `Unavailable(reason)` em vez de levantar excepção.
5. **Dependências pesadas** (rasterio, geopandas, streamlit) ficam em extras; o núcleo importa sem elas sempre que possível.
6. **Testes:** todo o código de cálculo tem testes com dados sintéticos. Testes que precisam de rede levam `@pytest.mark.network`.
7. **Valores científicos novos** ([A CALIBRAR]) são documentados em `docs/05-pipeline-analise.md`.
8. **Decisões relevantes** vão para `docs/10-decisoes-questoes-abertas.md` como ADR.

## Fluxo de trabalho

- Ramo por tarefa: `feat/T-104-sentinel2`, `fix/...`, `docs/...`.
- Pull request para `main`; o CI (ruff, mypy, pytest) tem de passar.
- Actualize `CHECKLIST.md` ao concluir uma tarefa.
- Mensagens de commit curtas, no imperativo, referindo o ID da tarefa (ex.: `T-108: adiciona índice de argila`).

## Estilo

`ruff check .` e `ruff format .` antes de submeter. Tipos em todo o código de `src/`.
