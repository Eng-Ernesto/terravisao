# Checklist do projecto — TerraVisão MVP

Marque `[x]` ao concluir. IDs referem-se a [docs/08-plano-backlog.md](docs/08-plano-backlog.md) e [docs/02-requisitos.md](docs/02-requisitos.md).

## Fase 0 — Fundações e spikes

- [x] Documentação do MVP escrita (docs/01–11)
- [x] Nome oficial decidido: TerraVisão (ADR-10)
- [x] Decisão de interface: Streamlit 2D + 3D opcional com pydeck (ADR-11)
- [x] Repositório criado e esqueleto do projecto (T-101)
- [x] T-001 Confirmar cobertura OneGeology para Angola (Q-01)
- [x] T-002 Spike Sentinel-2 via STAC e composto (Q-02)
- [x] T-003 Spike SRTM, declive e hillshade
- [ ] T-004 Spike extracção de lineamentos
- [ ] T-005 Spike desenho de polígono no Streamlit (Q-05)
- [ ] T-006 Medir tempo/memória para 10 km² e 2 500 km²
- [ ] T-007 Spike vista 3D com pydeck (Q-13)
- [x] Geofísico revisor: o dono do projecto (Q-11)
- [ ] Obter ficheiros do protótipo Longonjo (QGIS, amostras, Streamlit)

## Fase 1 — Núcleo de análise

- [x] T-102 `aoi`: validação, fronteira de Angola, UTM automático
- [x] T-103 `cache` com chaves e metadados
- [x] T-104 Ingestão Sentinel-2 com máscara e composto
- [x] T-105 Ingestão SRTM com preenchimento de vazios
- [ ] T-106 Ingestão Landsat
- [ ] T-107 Ingestão geologia (código pronto; decisão: seguir sem geologia, confiança no máximo "média"; shapefile BGS fica opcional)
- [x] T-108 Índices espectrais (testes com valores conhecidos)
- [x] T-109 Derivadas de terreno (declive, hillshade, drenagem, bacias, TWI)
- [x] T-110 Lineamentos e densidade
- [ ] T-111 Tabela de litologia e favorabilidade (código pronto; regras por preencher com geofísico)
- [x] T-112 Pontuação, classes, renormalização de camadas ausentes
- [x] T-113 Zonas
- [x] T-114 `pipeline.run` e proveniência
- [x] Afinar zonas: suavização de 100 m e área mínima 0,05 km²; Longonjo passou a gerar 1 a 2 zonas por alvo (6 a 26 ha). Limiares ainda por calibrar com geofísico
- [x] Acelerar descarga: opções GDAL (sem listar bucket, HTTP/2) e sem banda verde. Medido sem cache: 28 km² em 1 min 24 s (antes 7 min 53 s); 389 km² em 2 min 25 s. 2 500 km² por medir (T-006)
- [ ] T-115 Testes com rasters sintéticos e uma AOI real
- [x] CLI `terravisao run <aoi.geojson>` produz GeoTIFF e GeoJSON (corrido em Longonjo 5×5 km; falta verificar reprodutibilidade e T-115)

## Fase 2 — Interface e relatório

- [x] Direção visual definida (docs/12) e ecrã de resultados com dados reais de Longonjo (mapa, camadas, zonas); falta desenho do terreno e execução da análise na app
- [x] T-201 App: desenho de polígono/rectângulo e upload de GeoJSON, com validação (falta: coordenadas manuais e KML)
- [x] T-202 Selecção de alvos (falta: opções avançadas)
- [x] T-203 Barra de progresso por etapa (falta: cancelamento)
- [x] T-204 Camadas e probabilidade no mapa (sobre dados de demonstração)
- [x] T-205 Resumo, tabela de zonas e contribuições (sem cartões)
- [x] T-206 Recomendações por zona (método de campo sugerido na tabela e no PDF do TerraVisão)
- [x] T-207 Relatório PDF (8 páginas, ~750 KB: resumo, mapas, zonas, camadas de apoio, metodologia, limitações, proveniência)
- [x] T-208 Exportação GeoTIFF/GeoJSON/JSON (zip na app)
- [ ] T-209 Mensagens de erro e estados (parcial: erros de dados legíveis na análise de mapa e validação do terreno no TerraVisão)
- [ ] T-210 Vista 3D opcional (RF-24) — adiada, fora do âmbito de 24/11 (doc 14)
- [x] T-211 Assistente: lê só o resumo estruturado da análise (`Analysis.summary()`), sem aceder a ficheiros
- [ ] T-212 Assistente: filtros de zonas em linguagem natural (RF-26) — não implementado; fica para a fase seguinte
- [x] T-213 Assistente: fornecedor Cloudflare Workers AI, recurso a outros modelos e tratamento de indisponibilidade (testado com o serviço real)
- [x] T-214 Assistente: painel de chat; aviso de envio à Cloudflare na caixa de configuração (sem confirmação explícita ainda)
- [ ] T-215 Assistente: texto do relatório (o PDF tem interpretação automática; o texto da IA ainda não entra no PDF)
- [ ] T-216 Assistente: testes de avaliação (existem testes com respostas simuladas e `scripts/e2e_workers_ai.py` manual; falta automatizar)
- [x] Fluxo desenho → resultado → PDF funciona (marco M2): testado em Longonjo, 46,8 km² em cerca de 1 min

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
- [x] Fornecedor do assistente decidido: Cloudflare Workers AI com token do utilizador (ADR-15)
- [x] Modelo do Workers AI escolhido por teste real (Q-16, ADR-22)
- [x] Anomalias: classificação por quantis/desvios e zonas entram; detecção não supervisionada (Isolation Forest) fica de fora (Q-15)
- [x] A app funciona com o assistente desligado (modo offline por defeito; testes de render)
- [x] Distribuição por Docker local decidida (ADR-12)
- [ ] Dockerfile e docker compose testados (build e arranque) — a testar no outro computador seguindo docs/13-guia-docker.md
- [x] Dados de demonstração pré-calculados (Longonjo e Lubango/Huíla, com imagem de satélite)
- [x] App 100% offline: fontes, Leaflet e fronteiras de Angola locais; base de satélite offline (Sentinel-2 RGB); confirmado que não há pedidos externos
- [x] Guia de execução e validação em Docker (docs/13)
- [x] Validação do terreno com a fronteira real de Angola (T-102)
- [ ] Atribuição de dados (Copernicus, USGS, OneGeology) na app e no PDF
- [ ] Documentação de instalação testada em Windows e Linux
- [ ] Notebook Colab equivalente ao pipeline

## GeoExplora IA (24 de Novembro)

- [x] Produto e módulos definidos; âmbito e justificações no doc 14 (ADR-17 a ADR-21)
- [x] Núcleo `geoexplora`: leitura de CSV, GeoJSON, Shapefile e GeoTIFF; TREO e NdPr/TREO; outros elementos críticos
- [x] Classes de anomalia, superfície, zonas com teste de permutação, correlações, modelo com validação espacial
- [x] Derivadas magnéticas (1.ª vertical, gradiente horizontal, sinal analítico)
- [x] Dois conjuntos de demonstração (equipa; modelo sintético coerente), rotulados como fictícios
- [x] Assistente de IA: modo offline completo; Cloudflare Workers AI escrito e testado com respostas simuladas
- [x] Assistente com IA testado contra o Workers AI real (via CLI `cf`); modelo escolhido por teste (ADR-22)
- [ ] Pedido HTTP directo com token de API, noutra máquina (ensaiar antes da apresentação)
- [x] Relatório técnico em PDF; amostras classificadas em CSV
- [x] Interface com os módulos «Análise de mapa» e «TerraVisão (satélite)»
- [x] Roteiro de demonstração (doc 15)
- [ ] RTP (redução ao pólo), validado pelo geofísico
- [ ] Dados reais (geofísica, geoquímica, geologia) e validação científica
- [ ] Teste do Docker no outro computador
