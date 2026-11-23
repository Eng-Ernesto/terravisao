# Checklist do projecto — TerraVisão MVP

Marque `[x]` ao concluir. IDs referem-se a [docs/08-plano-backlog.md](docs/08-plano-backlog.md) e [docs/02-requisitos.md](docs/02-requisitos.md).

## Fase 0 — Fundações e spikes

- [x] Documentação do MVP escrita (docs/01–11)
- [x] Nome oficial decidido: TerraVisão (ADR-10)
- [x] Decisão de interface: Streamlit 2D + 3D opcional com pydeck (ADR-11)
- [x] Repositório criado e esqueleto do projecto (T-101)
- [ ] T-001 Confirmar cobertura OneGeology para Angola (Q-01)
- [ ] T-002 Spike Sentinel-2 via STAC e composto (Q-02)
- [ ] T-003 Spike SRTM, declive e hillshade
- [ ] T-004 Spike extracção de lineamentos
- [ ] T-005 Spike desenho de polígono no Streamlit (Q-05)
- [ ] T-006 Medir tempo/memória para 10 km² e 2 500 km²
- [ ] T-007 Spike vista 3D com pydeck (Q-13)
- [ ] Identificar geofísico revisor (Q-11)
- [ ] Obter ficheiros do protótipo Longonjo (QGIS, amostras, Streamlit)

## Fase 1 — Núcleo de análise

- [ ] T-102 `aoi`: validação, fronteira de Angola, UTM automático
- [ ] T-103 `cache` com chaves e metadados
- [ ] T-104 Ingestão Sentinel-2 com máscara e composto
- [ ] T-105 Ingestão SRTM com preenchimento de vazios
- [ ] T-106 Ingestão Landsat
- [ ] T-107 Ingestão geologia
- [ ] T-108 Índices espectrais (testes com valores conhecidos)
- [ ] T-109 Derivadas de terreno (declive, hillshade, drenagem, bacias, TWI)
- [ ] T-110 Lineamentos e densidade
- [ ] T-111 Tabela de litologia e favorabilidade
- [ ] T-112 Pontuação, classes, renormalização de camadas ausentes
- [ ] T-113 Zonas
- [ ] T-114 `pipeline.run` e proveniência
- [ ] T-115 Testes com rasters sintéticos e uma AOI real
- [ ] CLI `terravisao run <aoi.geojson>` produz GeoTIFF e GeoJSON reprodutíveis (marco M1)

## Fase 2 — Interface e relatório

- [ ] T-201 App: desenho, upload, coordenadas
- [ ] T-202 Selecção de alvos e opções avançadas
- [ ] T-203 Progresso e cancelamento
- [ ] T-204 Camadas e probabilidade no mapa
- [ ] T-205 Cartões de resumo, tabela de zonas, contribuições
- [ ] T-206 Recomendações por zona
- [ ] T-207 Relatório PDF
- [ ] T-208 Exportação GeoTIFF/GeoJSON/JSON
- [ ] T-209 Mensagens de erro e estados
- [ ] T-210 Vista 3D opcional (RF-24)
- [ ] Fluxo desenho → resultado → PDF funciona (marco M2)

## Fase 3 — Validação e piloto

- [ ] T-301 Áreas de teste (Longonjo, Huíla) processadas e documentadas
- [ ] T-302 Revisão de pesos e limiares com geofísico (Q-03, Q-04)
- [ ] T-303 Análise de sensibilidade
- [ ] T-304 Comparação com pontos MRDS/MINDAT
- [ ] T-305 Piloto com ≥ 5 utilizadores
- [ ] T-306 Ajustes a partir do feedback
- [ ] MVP validado (marco M3)

## Transversal

- [x] CI de testes e lint no GitHub
- [ ] Termos de uso e aviso legal (Q-10)
- [ ] Decisão de hospedagem da demonstração (Q-07)
- [ ] Atribuição de dados (Copernicus, USGS, OneGeology) na app e no PDF
- [ ] Documentação de instalação testada em Windows e Linux
- [ ] Notebook Colab equivalente ao pipeline
