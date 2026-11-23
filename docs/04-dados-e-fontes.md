# 04 — Dados e fontes

Todas as fontes são gratuitas. As licenças e os endpoints devem ser confirmados no momento da implementação (**[A VERIFICAR]**), pois mudam com o tempo.

## 1. Resumo

| Dado | Fonte | Resolução | Uso |
|---|---|---|---|
| Sentinel-2 L2A | Copernicus Data Space Ecosystem (STAC/openEO) ou AWS/Planetary Computer | 10–20 m | Óxido de ferro, argila, NDVI |
| Landsat 8/9 C2 L2 | USGS (EarthExplorer) via STAC/AWS/Planetary Computer | 30 m | Validação cruzada, histórico |
| SRTM 1 arc-sec | USGS / NASA (ou Copernicus DEM GLO-30 como alternativa) | ~30 m | Elevação, declive, lineamentos, drenagem |
| Geologia | OneGeology (WMS/WFS) e cartas geológicas de Angola | Típica 1:1 000 000 [A VERIFICAR] | Litologia, falhas mapeadas |
| Ocorrências minerais conhecidas | USGS MRDS, MINDAT (uso conforme licença) | Pontos | Validação, não entrada do MVP |

## 2. Sentinel-2 L2A

Bandas usadas:

| Banda | Nome | Resolução | Uso |
|---|---|---|---|
| B02 | Azul | 10 m | Óxido de ferro |
| B03 | Verde | 10 m | NDWI |
| B04 | Vermelho | 10 m | Óxido de ferro, NDVI |
| B08 | NIR | 10 m | NDVI |
| B8A | NIR estreito | 20 m | Ferroso |
| B11 | SWIR 1 | 20 m | Argila, ferroso |
| B12 | SWIR 2 | 20 m | Argila |
| SCL | Classificação de cena | 20 m | Máscara de nuvem/sombra/água |

Regras:
- Reamostrar bandas de 20 m para 10 m, ou trabalhar tudo a 20 m para o MVP (**decisão de simplicidade: 20 m**, ver doc 10).
- Filtrar cenas com nuvens < 20 % [A CALIBRAR].
- Janela temporal por defeito: Maio–Setembro (época seca) dos últimos 2–3 anos, composto por **mediana** de píxeis válidos.
- Se não houver píxeis válidos suficientes, alargar a janela e avisar.

## 3. Landsat 8/9 Collection 2 Level 2

| Banda | Nome | Resolução |
|---|---|---|
| B2 | Azul | 30 m |
| B4 | Vermelho | 30 m |
| B5 | NIR | 30 m |
| B6 | SWIR 1 | 30 m |
| B7 | SWIR 2 | 30 m |
| QA_PIXEL | Máscara | 30 m |

Usado para: validação cruzada dos índices do Sentinel-2 e fallback quando o Sentinel-2 falha. Landsat tem escala e offset próprios (aplicar os factores da Collection 2).

## 4. SRTM

- Tile de 1° × 1°, 1 arc-sec (~30 m), CRS WGS84 (EPSG:4326).
- Preencher vazios (voids) por interpolação antes dos cálculos.
- Reprojectar para o UTM da AOI antes de derivar declive e hidrologia.
- Observação: SRTM é modelo de superfície, afectado por vegetação densa. Aviso na documentação do relatório.

## 5. Geologia

- **OneGeology:** serviço WMS/WFS do mapa geológico global/regional. Verificar se existe cobertura de Angola com atributos litológicos úteis [A VERIFICAR]. Se só houver WMS (imagem), a litologia não é utilizável como dado; nesse caso considerar vectorização manual.
- **Alternativa/complemento:** cartas geológicas digitalizadas e georreferenciadas a partir de fontes oficiais (Instituto Geológico de Angola) e do mapa USGS/regional.
- **Tabela de regras:** `data/reference/litologia_regras.csv` mapeia unidade/litologia → favorabilidade (0, 0.5, 1) por alvo. Preenchida e validada por geofísico. Exemplo de estrutura:

| unidade | litologia | ferro | cobre | ouro | agua |
|---|---|---|---|---|---|
| (código OneGeology) | quartzito ferruginoso / BIF | 1.0 | 0.2 | 0.4 | 0.2 |
| | granito-gnaisse | 0.2 | 0.3 | 0.4 | 0.4 |
| | aluvião | 0.0 | 0.0 | 0.1 | 0.9 |

Os valores acima são **ilustrativos**.

## 6. Cache

- Pasta `data/cache/`, fora do git.
- Chave: `{fonte}/{hash(aoi_bbox)}/{datas}/{versao_algoritmo}`.
- Guardar metadados junto: IDs das cenas, data, nuvens, versão do pipeline.
- Política de limpeza: manual no MVP, com comando CLI `terravisao cache clear`.

## 7. Qualidade e proveniência

Cada resultado guarda: IDs das cenas, datas, % nuvens do composto, % de píxeis mascarados, versões do código e dos pesos. Isto vai para o relatório (RNF-03).

## 8. Licenças e atribuição

- Sentinel-2/Copernicus: livre, com atribuição ("Contains modified Copernicus Sentinel data").
- Landsat/USGS: domínio público, com citação recomendada.
- SRTM: domínio público.
- OneGeology: verificar licença da camada concreta antes de redistribuir.
- Ocorrências MRDS/MINDAT: verificar termos antes de incluir no produto.
