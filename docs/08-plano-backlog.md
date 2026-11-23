# 08 — Plano e backlog

Não há datas fixas: as fases são sequenciais e cada uma tem critério de saída. Estimativas em esforço relativo (S/M/L).

## Fase 0 — Spikes (reduzir incerteza)

Objectivo: confirmar o que pode bloquear o MVP antes de construir.

| ID | Tarefa | Esforço | Saída |
|---|---|---|---|
| T-001 | Confirmar cobertura e atributos do OneGeology para Angola (WMS/WFS, escala, licença) | S | Decisão: geologia como vector, como imagem ou digitalização própria |
| T-002 | Descarregar Sentinel-2 de uma AOI via STAC (Copernicus ou Planetary Computer) e gerar composto | M | Notebook Colab a funcionar |
| T-003 | Obter SRTM de uma AOI e derivar declive/hillshade | S | Notebook |
| T-004 | Testar extracção de lineamentos de hillshade | M | Exemplo visual comparado com falhas mapeadas |
| T-005 | Testar widget de desenho de polígono (folium Draw vs leafmap) no Streamlit | S | Decisão no doc 10 |
| T-007 | Testar pydeck `TerrainLayer` no Streamlit com um raster SRTM e uma textura de índice (desempenho e WebGL) | S | Confirma viabilidade do RF-24 |
| T-006 | Medir tempo e memória para 10 km² e 2 500 km² | S | Limites realistas de área |

**Saída da fase:** questões Q-01, Q-02 e Q-05 do doc 10 respondidas.

## Fase 1 — Núcleo de análise (sem UI)

| ID | Tarefa | Req. | Esforço |
|---|---|---|---|
| T-101 | Scaffold do repositório, `pyproject`, CI de testes, `.gitignore` | RNF-05 | S |
| T-102 | `aoi.py`: validação, fronteira de Angola, UTM automático | RF-01..04 | S |
| T-103 | `cache.py` com chaves e metadados | RF-10 | S |
| T-104 | `ingest/sentinel2.py` com máscara e composto | RF-06, RF-12 | M |
| T-105 | `ingest/srtm.py` com preenchimento de vazios | RF-08 | S |
| T-106 | `ingest/landsat.py` | RF-07 | M |
| T-107 | `ingest/geology.py` | RF-09 | M |
| T-108 | `indices.py` com testes de valores conhecidos | RF-11 | S |
| T-109 | `terrain.py`: declive, hillshade, drenagem, bacias, TWI | RF-13 | M |
| T-110 | Lineamentos e densidade | RF-13 | M |
| T-111 | Tabela de litologia e `lithology_favorability` | RF-14 | M |
| T-112 | `scoring.py`: normalização, pesos, classes, renormalização de camadas ausentes | RF-15, RF-16 | M |
| T-113 | `zones.py` | RF-17 | M |
| T-114 | `pipeline.run` + `Provenance` | RNF-03 | M |
| T-115 | Testes com mini-rasters sintéticos e uma AOI real | RNF-09 | M |

**Saída da fase:** script CLI que, dada uma AOI GeoJSON, produz GeoTIFFs e GeoJSON de zonas, reprodutíveis.

## Fase 2 — Interface e relatório

| ID | Tarefa | Req. | Esforço |
|---|---|---|---|
| T-201 | App Streamlit: desenho, upload, coordenadas | RF-01, RF-02 | M |
| T-202 | Selecção de alvos e opções avançadas | RF-05 | S |
| T-203 | Progresso e cancelamento | US-04 | M |
| T-204 | Visualização de camadas e probabilidade | RF-18 | M |
| T-211 | Assistente: ferramentas sobre o resultado (`tools.py`) e testes sem LLM | RF-25 | M |
| T-212 | Assistente: filtros estruturados com validação (`filters.py`) | RF-26 | M |
| T-213 | Assistente: fornecedor Cloudflare Workers AI (token do utilizador), testar modelos disponíveis no plano gratuito e a qualidade em português; tratamento de erros e indisponibilidade | RF-29, RF-30 | M |
| T-214 | Assistente: painel de chat no Streamlit, consentimento e indicador de modo | RF-25, RF-29 | M |
| T-215 | Assistente: texto do relatório (modelos fixos + LLM) e integração no PDF | RF-27 | M |
| T-216 | Assistente: testes de avaliação (perguntas de referência, recusa de afirmações de certeza, citação de valores) | RF-28 | M |
| T-210 | Vista 3D opcional com pydeck (relevo + camada + zonas), depois de T-204 | RF-24 | M |
| T-205 | Cartões de resumo, tabela de zonas, contribuições | RF-19, RNF-04 | M |
| T-206 | Recomendações por zona | RF-20 | S |
| T-207 | Relatório PDF | RF-21, RF-23 | M |
| T-208 | Exportação GeoTIFF/GeoJSON/JSON | RF-22 | S |
| T-209 | Mensagens de erro e estados (doc 06 §6) | US-11 | S |

## Fase 3 — Validação e piloto

| ID | Tarefa | Esforço |
|---|---|---|
| T-301 | Correr áreas de teste (Longonjo, Huíla) e documentar | M |
| T-302 | Sessão de revisão de pesos/limiares com geofísico | M |
| T-303 | Análise de sensibilidade | S |
| T-304 | Comparação com pontos MRDS/MINDAT (razão de enriquecimento) | M |
| T-305 | Piloto com ≥ 5 utilizadores e recolha de feedback | M |
| T-306 | Ajustar pesos/UX com base nos resultados | M |

## Definição de pronto (por tarefa)

- Código com testes automáticos relevantes a passar.
- Docstring dos módulos públicos.
- Parâmetros científicos novos em `config` e referidos no doc 05.
- Sem dependência paga.
- Se muda comportamento visível, documento correspondente actualizado.

## Marcos

| Marco | Critério |
|---|---|
| M0 Spikes concluídos | Fontes e riscos confirmados |
| M1 Pipeline CLI | 1 AOI real processada ponta a ponta |
| M2 App usável | Fluxo desenho → resultado → PDF |
| M3 MVP validado | Revisão por geofísico + piloto |

## Roadmap pós-MVP

1. Dados geofísicos (magnetometria, radiometria K/Th/U) — ver anexo do protótipo.
2. Modelo supervisionado com ocorrências conhecidas.
3. ASTER e outros sensores para mineralogia.
4. Contas de utilizador, histórico de análises, partilha.
5. Execução em segundo plano / fila para áreas grandes.
6. Mais minerais (diamantes, manganês, fosfato, etc.).
7. API pública e integração com outras plataformas.
8. Loop de feedback: resultados de campo melhoram os pesos.
