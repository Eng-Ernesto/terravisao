# 03 — Arquitectura

## 1. Visão geral

Aplicação Python monolítica em camadas. A UI (Streamlit) só orquestra; toda a lógica científica vive num pacote independente `terravisao`, testável sem interface e reutilizável em notebooks Colab.

```
┌──────────────────────────────────────────────┐
│ UI  (Streamlit + folium/leafmap + Draw)      │
└───────────────┬──────────────────────────────┘
                │ AnalysisRequest
┌───────────────▼──────────────────────────────┐
│ Orquestrador (pipeline.run)                  │
└──┬────────┬──────────┬──────────┬────────────┘
   │        │          │          │
┌──▼───┐ ┌──▼────┐ ┌───▼─────┐ ┌──▼─────┐
│Ingest│ │Indices│ │Terrain  │ │Geology │   camadas de entrada
└──┬───┘ └──┬────┘ └───┬─────┘ └──┬─────┘
   └────────┴────┬─────┴──────────┘
            ┌────▼─────┐
            │ Scoring  │  normalização + pesos + classes
            └────┬─────┘
            ┌────▼─────┐
            │ Zones    │  agrupamento e ranking
            └────┬─────┘
            ┌────▼─────┐
            │ Report   │  mapas, PDF, GeoTIFF, GeoJSON
            └──────────┘
        Cache local (disco) em todos os passos
```

## 2. Fluxo de uma análise

1. UI recolhe geometria e alvos → `AnalysisRequest`.
2. Validação (Angola, geometria, área).
3. Fuso UTM da AOI escolhido automaticamente (Angola cobre 32S, 33S e 34S; ex.: Longonjo usa EPSG:32733).
4. `ingest`: obtém Sentinel-2, Landsat, SRTM, geologia (com cache).
5. `indices`: calcula índices espectrais sobre composto sem nuvens.
6. `terrain`: deriva declive, lineamentos, drenagem, bacias, TWI.
7. `geology`: reclassifica litologia por alvo.
8. `scoring`: normaliza, pondera, classifica por alvo.
9. `zones`: agrupa classe Alta em zonas e ordena.
10. `report`: gera mapas, tabelas, PDF e exports.
11. UI mostra resultados e botões de download.

## 3. Stack

| Camada | Tecnologia | Nota |
|---|---|---|
| Linguagem | Python 3.11+ | |
| UI | Streamlit | Alinhado com o protótipo anterior |
| Mapa 2D | folium + streamlit-folium (Draw) ou leafmap | Decidir no spike (ver doc 10) |
| Vista 3D (opcional) | pydeck (deck.gl) com `TerrainLayer` e `GeoJsonLayer` | Nativo no Streamlit, sem JavaScript próprio. Ver ADR-11 |
| Raster | rasterio, rioxarray, numpy | |
| Vector | geopandas, shapely, pyproj | |
| Pesquisa de imagens | pystac-client + odc-stac (ou stackstac) | STAC do Copernicus Data Space / Planetary Computer / AWS |
| Derivadas de terreno | scipy, scikit-image, whitebox ou richdem | Lineamentos e hidrologia |
| ML | scikit-learn | Fase 2; no MVP só utilitários (normalização, clustering opcional) |
| Relatório | matplotlib + reportlab ou WeasyPrint | |
| Assistente (opcional) | Interface `LLMProvider` com fornecedores intermutáveis (API do Claude, modelo local via Ollama, modo offline com modelos fixos) | Ver ADR-14 |
| Testes | pytest | |
| Protótipo | Google Colab | Notebooks em `notebooks/` |
| Packaging | uv ou pip + `pyproject.toml` | |

## 4. Estrutura de pastas proposta

```
geofisica/
├── README.md
├── docs/
├── pyproject.toml
├── src/terravisao/
│   ├── config.py            # pesos, limiares, bandas, caminhos
│   ├── models.py            # AnalysisRequest, AnalysisResult (ver doc 07)
│   ├── aoi.py               # validação e UTM
│   ├── ingest/
│   │   ├── sentinel2.py
│   │   ├── landsat.py
│   │   ├── srtm.py
│   │   └── geology.py
│   ├── indices.py
│   ├── terrain.py
│   ├── scoring.py
│   ├── zones.py
│   ├── report/
│   │   ├── maps.py
│   │   └── pdf.py
│   ├── cache.py
│   └── pipeline.py
├── app/
│   └── streamlit_app.py
├── data/
│   ├── cache/               # ignorado pelo git
│   ├── reference/           # tabelas de litologia, áreas de teste
│   └── samples/             # AOI de exemplo, mini-rasters para testes
├── notebooks/
├── tests/
└── .gitignore
```

## 4.1 Assistente de chat (módulo opcional)

```
src/terravisao/assistant/
├── tools.py        # funções fixas sobre AnalysisResult: list_zones, zone_detail, compare_zones, layer_stats, warnings
├── filters.py      # esquema do filtro estruturado + validação + execução
├── provider.py     # interface LLMProvider + fornecedores (claude, ollama, offline)
├── prompts.py      # instruções de sistema (limitações, tom, proibições)
└── report_text.py  # texto do relatório (modelos fixos + versão com LLM)
```

Regras de desenho:
- O modelo **só vê** o que as funções de `tools.py` devolvem (JSON do resultado). Não tem acesso a rasters nem ao sistema de ficheiros.
- Filtros: o modelo devolve JSON (`{"target": "ferro", "min_area_km2": 0.1}`); `filters.py` valida contra um esquema e o código executa. Pedido inválido é recusado, nunca executado.
- Fornecedor escolhido por variáveis de ambiente (`TERRAVISAO_LLM=claude|ollama|offline`, `ANTHROPIC_API_KEY`). Chaves nunca entram no repositório.
- Sem fornecedor ou sem internet: `offline`, com respostas por modelos fixos para perguntas frequentes.
- Interface Streamlit: painel de chat lateral; nenhum cálculo científico passa por ele.

## 5. Princípios de implementação

- **Funções puras** nos módulos de cálculo: entram arrays/rasters e parâmetros, saem arrays/rasters.
- **Config central:** pesos, limiares e bandas num só sítio (`config.py` ou YAML) e gravados em cada resultado.
- **Cache por chave:** hash de (AOI, fonte, intervalo de datas, versão do algoritmo).
- **Falha parcial:** cada fonte devolve resultado ou `Unavailable(reason)`; o `scoring` redistribui pesos entre camadas disponíveis e avisa.
- **Sem estado oculto na UI:** o Streamlit só guarda `AnalysisRequest` e `AnalysisResult` no `session_state`.
- **Execução longa:** no MVP corre síncrona com barra de progresso; se passar dos limites, passa para processo em segundo plano (fase 2).

## 6. Implantação (MVP)

- Local: `streamlit run app/streamlit_app.py`.
- Demonstração partilhada: Streamlit Community Cloud, Hugging Face Spaces ou VM gratuita, a confirmar conforme limites de memória e disco. Terrenos grandes podem exceder os limites gratuitos; por isso a área máxima é restrita.
- Colab: notebook que importa o pacote e corre o pipeline para uso de geofísicos avançados.
