# 05 — Pipeline de análise

Método: **sobreposição multicritério ponderada** (weighted overlay) sobre camadas normalizadas. Não há modelo de machine learning treinado no MVP: não existem dados rotulados fiáveis (ocorrências confirmadas) para Angola neste momento. Os pesos são heurísticas geológicas a validar por geofísico (**[A CALIBRAR]**).

## 1. Pré-processamento

1. Recortar todos os rasters à AOI com margem (buffer 1 km) para evitar efeitos de borda em derivadas.
2. Reprojectar para o UTM da AOI; grelha comum (20 m no MVP).
3. Máscaras:
   - Nuvem/sombra/neve: SCL (Sentinel-2), QA_PIXEL (Landsat).
   - Água: NDWI > 0 ou SCL = água.
   - Vegetação densa: NDVI > 0.4 [A CALIBRAR] (os rácios espectrais perdem validade com cobertura vegetal).
4. Composto por mediana temporal de píxeis válidos.
5. Guardar a **fracção de píxeis válidos** por camada; usada como indicador de confiança.

## 2. Índices espectrais

Fórmulas para Sentinel-2 (equivalentes Landsat entre parêntesis):

| Índice | Fórmula | Realça |
|---|---|---|
| Óxido de ferro (férrico) | B04 / B02 (L: B4 / B2) | Hematite, goethite, gossans |
| Ferroso | B11 / B8A (L: B6 / B5) | Minerais com Fe²⁺ |
| Argila / hidroxilos | B11 / B12 (L: B6 / B7) | Alteração argilosa, sericite, caulinite |
| NDVI | (B08 − B04) / (B08 + B04) | Vegetação (máscara) |
| NDWI | (B03 − B08) / (B03 + B08) | Água superficial (máscara) |

Passos: calcular → recortar valores extremos pelos percentis 2 e 98 → guardar o raster do índice (em GeoTIFF) para o mapa temático.

Nota: ouro e cobre não têm assinatura espectral directa. Realça-se **alteração hidrotermal associada** (óxido de ferro + argila) e litologia/estrutura favoráveis. Isto indica **contexto favorável**, não ouro ou cobre.

## 3. Camadas de terreno (SRTM)

| Camada | Método | Uso |
|---|---|---|
| Elevação | SRTM preenchido e reprojectado | Mapa base |
| Declive | gradiente (graus) | Água (zonas planas acumulam), ferro (cristas) |
| Hillshade multi-azimute | 4–8 azimutes (ex.: 0°, 45°, 90°, 135°…) | Realce estrutural, entrada de lineamentos |
| Lineamentos | Hillshade → realce de bordas (Canny) → Hough/segmentos → filtro de comprimento mínimo | Falhas/fracturas prováveis |
| Densidade de lineamentos | Comprimento por km² (kernel) | Água subterrânea (permeabilidade secundária), mineralização estrutural |
| Rede de drenagem | Preencher depressões → direcção de fluxo → acumulação → limiar | Bacias, água |
| Bacias | Delimitação a partir da acumulação | Mapa de bacias |
| TWI | ln(área contribuinte / tan(declive)) | Acumulação de humidade → água |
| Densidade de drenagem | Comprimento de linhas de água por km² | Água (baixa densidade → maior infiltração) |

Lineamentos de MDE são **candidatos**, não falhas confirmadas; a UI deve rotulá-los como tal e, quando existirem, mostrar as falhas do mapa geológico à parte.

## 4. Camada geológica

1. Intersectar polígonos geológicos com a AOI.
2. Mapear unidade → favorabilidade por alvo via `litologia_regras.csv` (valores 0–1).
3. Rasterizar à grelha comum.
4. Se não houver cobertura geológica: camada marcada `Unavailable`; peso redistribuído; relatório e confiança reflectem isto.

## 5. Normalização

Cada camada entra no `scoring` numa escala **0–1**:

- Índices contínuos: normalização por percentis (2º–98º) dentro da AOI → 0–1. Aviso: é relativa à AOI, não absoluta. Para absoluta, calibrar com valores de referência regionais (fase 2).
- Camadas com sentido inverso (ex.: declive alto desfavorável à água): inverter (1 − x).
- Camadas categóricas (litologia): usar directamente a tabela de favorabilidade.

## 6. Pesos por alvo [A CALIBRAR]

Soma por alvo = 1. Pontos de partida para discussão com geofísico:

| Camada | Ferro | Cobre | Ouro | Água |
|---|---|---|---|---|
| Óxido de ferro | 0.35 | 0.15 | 0.20 | — |
| Ferroso | 0.10 | — | — | — |
| Argila/hidroxilos | 0.10 | 0.25 | 0.20 | — |
| Litologia | 0.30 | 0.30 | 0.25 | 0.25 |
| Densidade de lineamentos | 0.10 | 0.25 | 0.30 | 0.25 |
| Declive (inv.) | 0.05 | 0.05 | 0.05 | 0.15 |
| TWI | — | — | — | 0.15 |
| Densidade de drenagem (inv.) | — | — | — | 0.10 |
| NDVI (humidade/vegetação) | — | — | — | 0.10 |

Os valores acima são ponto de partida para discussão, não resultado de calibração.

Fórmula: `score(pixel) = Σ (peso_i × camada_i(pixel))`, só sobre camadas disponíveis, com pesos renormalizados.

## 7. Classificação

| Classe | Limiar (score) [A CALIBRAR] |
|---|---|
| Baixa | < 0.40 |
| Média | 0.40 – 0.65 |
| Alta | ≥ 0.65 |

Antes de classificar, a pontuação é suavizada com um filtro gaussiano que ignora NaN (`score_smoothing_m = 100 m`), para evitar zonas fragmentadas por ruído de pixel. Os limiares aplicam-se ao raster suavizado. O resultado "final" por alvo para a AOI inteira usa a **fracção da área em classe Alta/Média** e a pontuação máxima de zona, segundo regra a fixar:

- **Alta** se existir uma zona ≥ `final_high_zone_km2` (0.5 km²) [A CALIBRAR], ou ≥ 10 % da AOI em Alta.
- **Média** se não for Alta e existir alguma zona (≥ `min_zone_area_km2` = 0.05 km², 5 ha), ou ≥ 20 % da AOI em Média+Alta.
- **Baixa** nos restantes casos.

## 8. Zonas

1. Máscara binária de classe Alta (ou Média+ se não houver Alta).
2. Limpeza morfológica (remover ruído < 5 píxeis; fechar pequenos buracos).
3. Componentes ligados → polígonos.
4. Filtrar por área mínima.
5. Ordenar por pontuação média × área; nomear Zona A, B, C…
6. Para cada zona: área, centroide, pontuação média, contribuição por camada (RNF-04), recomendação de campo.

## 9. Recomendação de método de campo

Tabela de regras simples, em `data/reference/recomendacoes.csv`:

| Alvo | Método sugerido |
|---|---|
| Ferro | Magnetometria; amostragem de superfície |
| Cobre | Polarização induzida (IP) e magnetometria; geoquímica de solo |
| Ouro | Geoquímica de solo/sedimento de corrente; magnetometria; IP |
| Água | Resistividade (SEV/tomografia); verificar com furos existentes |

São sugestões de planeamento, a confirmar por geofísico.

## 10. Confiança

Cada alvo/zona recebe um indicador de confiança (Alta/Média/Baixa) baseado em:
- fracção de píxeis válidos (nuvem, vegetação);
- disponibilidade de geologia;
- coerência entre Sentinel-2 e Landsat (se calculado);
- escala do mapa geológico.

Isto é diferente da probabilidade e aparece lado a lado com ela.

## 11. Validação

1. **Casos conhecidos:** correr o pipeline em áreas com ocorrências ou prospecção conhecida (Longonjo é o primeiro candidato, ver anexo) e ver se as zonas Alta coincidem.
2. **Pontos MRDS/MINDAT:** medir quantos pontos conhecidos caem em Alta/Média vs. área total (razão de enriquecimento). Só para avaliação.
3. **Revisão por geofísico:** sessão de revisão dos mapas e pesos.
4. **Sensibilidade:** variar pesos ±20 % e ver quanto as zonas mudam; reportar zonas estáveis.

## 12. Fase 2 (fora do MVP)

- Magnetometria e radiometria (canais K, Th, U) — já previstas no protótipo anterior.
- Modelo supervisionado (scikit-learn) quando existir conjunto de ocorrências/negativos fiável.
- ASTER (SWIR/TIR) para melhor mineralogia.
- Séries temporais para humidade/água.
- Integração dos resultados do campo (feedback loop).
