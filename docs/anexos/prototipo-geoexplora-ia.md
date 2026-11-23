# Anexo — Protótipo anterior: GeoExplora IA

Resumo do ficheiro `Document 4.pdf` ("Estrutura tecnológica do GeoExplora IA"). Serve de contexto e de fonte de requisitos para a fase 2.

> Nota: o PDF usa o nome **GeoExplora IA**, que é o protótipo anterior. O nome oficial do produto é **TerraVisão** (ADR-10 no doc 10).

## Arquitectura funcional

1. **Aquisição e integração de dados:** geológicos, geofísicos, topográficos, geoquímicos.
2. **Processamento e análise espacial (QGIS):** preparação, organização, sobreposição de camadas.
3. **Inteligência artificial (Python):** análise multicritério, classificação, modelação.
4. **Geração de resultados:** mapas temáticos, anomalias, mapa de favorabilidade mineral.
5. **Interface:** dashboard interactivo em Streamlit.

## Seis módulos da plataforma

| Módulo | Função |
|---|---|
| 01 Visão geral | Apresentar o projecto e indicadores |
| 02 Exploração de dados | Consultar e integrar dados geológicos e geofísicos |
| 03 Análise geológica | Litologia, estruturas |
| 04 Análise geofísica | Anomalias magnéticas e radiométricas |
| 05 Inteligência artificial | Classificar favorabilidade |
| 06 Visualização cartográfica | Mapas, resultados e zonas de interesse |

## Dados necessários

| Tipo | Informação |
|---|---|
| Geológicos | Litologia, formações, unidades |
| Estruturais | Falhas, fracturas, lineamentos |
| Magnetométricos | Anomalias magnéticas |
| Radiométricos | Canais K, Th, U |
| Topográficos | Elevação, declive, relevo |
| Geoquímicos | Concentrações de elementos, quando disponíveis |

## Já desenvolvido

- Projecto QGIS de **Longonjo**.
- Sistema de referência WGS 84 / UTM 33S (EPSG:32733).
- Mapa de localização.
- Inserção e visualização de amostras.
- Classificação e representação de anomalias.
- Legenda e elementos cartográficos.
- Aplicação Streamlit.
- Painel de exploração inicial.

## Como se liga ao MVP TerraVisão

| Protótipo | Aproveitamento no MVP |
|---|---|
| Projecto QGIS de Longonjo | Primeira **área de teste** para validação (T-301) |
| EPSG:32733 | Confirma o uso de UTM 33S para esta região; o MVP escolhe o fuso por AOI |
| Amostras inseridas | Possível verdade de campo para validação; confirmar origem e permissão de uso |
| Streamlit inicial | Ponto de partida da UI (rever o que pode ser reaproveitado) |
| Dados magnéticos e radiométricos | **Fora do MVP**; entram na fase 2 |
| Módulos 01–06 | Inspiração para a navegação, mas o MVP usa fluxo linear Terreno → Resultado |

## Perguntas para o dono do protótipo

1. Onde estão o projecto QGIS, as amostras e o código Streamlit? Podem ser colocados em `data/reference/longonjo/` e `app/`?
2. As amostras de Longonjo têm resultados laboratoriais ou apenas localização?
3. Que dados magnéticos/radiométricos existem para Longonjo e qual a licença?
