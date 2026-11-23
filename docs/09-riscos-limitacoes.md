# 09 — Riscos e limitações

## 1. Limitações científicas (comunicar ao utilizador)

| # | Limitação | Impacto | Como é tratada |
|---|---|---|---|
| L-01 | Detecção remota vê a superfície, não o subsolo | Mineral profundo não é detectado | Aviso obrigatório; resultado é triagem |
| L-02 | Cobre e ouro não têm assinatura espectral directa | Só se detecta alteração associada | Texto do relatório explica "contexto favorável" |
| L-03 | Vegetação e solos cobertos mascaram os índices | Menos píxeis válidos, baixa confiança | Máscara NDVI, época seca, indicador de confiança |
| L-04 | Óxido de ferro aparece sem minério (laterite, solos ferruginosos) | Falsos positivos para ferro e ouro | Cruzar com litologia/estrutura; revisão por geofísico |
| L-05 | Mapa geológico a escala pequena (ex.: 1:1 000 000) | Litologia grosseira | Peso moderado, confiança reduzida |
| L-06 | Lineamentos do MDE não são falhas confirmadas | Estrutura pode ser artefacto | Rotulados como candidatos |
| L-07 | Normalização relativa à AOI | Em áreas "pobres", o melhor local parece Alto | Mostrar valores absolutos de índice; calibração regional na fase 2 |
| L-08 | Pesos são heurísticos, sem treino | Classificação pode não generalizar | Validação com casos conhecidos e geofísico |
| L-09 | Água subterrânea depende de hidrogeologia que o MVP não vê (aquíferos, profundidade) | Probabilidade grosseira | Aviso; recomendar resistividade e consulta a furos existentes |
| L-10 | SRTM é superfície, afectada por vegetação | Pequenos erros em declive e drenagem | Aviso |

## 2. Riscos técnicos

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | Sem cobertura utilizável do OneGeology para Angola | Média | Alto | Spike T-001; plano B: digitalizar carta geológica ou usar só índices + estrutura com confiança reduzida |
| R-02 | Nuvens frequentes (época chuvosa, norte) | Média | Médio | Compostos temporais, época seca, Landsat de reserva |
| R-03 | Limites de memória/tempo em hospedagem gratuita | Alta | Médio | Área máxima, resolução 20 m, cache, processamento por blocos |
| R-04 | APIs gratuitas mudam ou impõem quotas | Média | Médio | STAC aberto com mais de uma origem, cache, abstracção em `ingest` |
| R-05 | Lineamentos ruidosos | Média | Médio | Filtros de comprimento, multi-azimute, comparar com falhas mapeadas |
| R-06 | Fuso UTM errado perto de limites de zona | Baixa | Médio | Escolher o fuso pelo centroide, testar AOIs de fronteira |
| R-07 | Resultados não reprodutíveis (composto muda com novas cenas) | Média | Médio | Gravar IDs de cenas e datas; permitir reexecutar com mesmas cenas |
| R-08 | Dependências geoespaciais difíceis de instalar no Windows | Média | Baixo | `uv`/conda, documentar instalação, container |

## 3. Riscos de produto e responsabilidade

| # | Risco | Mitigação |
|---|---|---|
| P-01 | Utilizador trata "Alta" como garantia e investe | Linguagem de probabilidade, avisos em cada ecrã e PDF, termos de uso |
| P-02 | Expectativa de substituir o geofísico | Posicionamento claro como triagem; recomendações apontam métodos de campo |
| P-03 | Falsos negativos fazem desistir de áreas boas | Mostrar confiança; "Baixa" não é "não existe" |
| P-04 | Confidencialidade de terrenos dos clientes | Não partilhar nem treinar com dados sem consentimento (RNF-07) |
| P-05 | Questões legais sobre direitos mineiros e licenças em Angola | Fora do âmbito; avisar que a ferramenta não substitui o enquadramento legal |
| P-07 | O assistente inventa valores ou afirma certeza (alucinação) | Só lê dados do resultado por funções fixas, cita os valores, recusa afirmações de certeza e é testado com perguntas de referência (T-216) |
| P-08 | Dados do terreno enviados a um fornecedor externo | Modo offline por defeito; consentimento explícito antes de enviar; aviso visível (RNF-07) |
| P-09 | Chave de API exposta num repositório público | Chave só por variável de ambiente; `.env` no `.gitignore`; nada de chaves nos exemplos |
| P-06 | Dois nomes (TerraVisão e GeoExplora IA) confundem a equipa | Resolvido: TerraVisão é o nome oficial (ADR-10) |

## 4. Texto de aviso padrão

> Este resultado indica probabilidade com base em dados públicos de detecção remota (Sentinel-2, Landsat, SRTM e mapas geológicos). Não confirma a existência de minerais ou de água subterrânea, não substitui o trabalho de campo do geofísico nem a sondagem. Utilize-o para decidir onde confirmar, não para decidir se investe.
