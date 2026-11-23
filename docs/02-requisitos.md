# 02 — Requisitos

## 1. Histórias de utilizador

| ID | História | Prioridade |
|---|---|---|
| US-01 | Como utilizador, desenho o meu terreno no mapa para o analisar. | Must |
| US-02 | Como utilizador, introduzo coordenadas ou carrego GeoJSON/KML. | Should |
| US-03 | Como utilizador, escolho o que quero analisar (ferro, cobre, ouro, água). | Must |
| US-04 | Como utilizador, vejo o progresso da análise e uma estimativa de tempo. | Should |
| US-05 | Como utilizador, vejo mapas de óxido de ferro, argila, elevação/falhas/bacias. | Must |
| US-06 | Como utilizador, vejo a classificação final Alta/Média/Baixa por alvo. | Must |
| US-07 | Como utilizador, vejo zonas priorizadas (Zona A, B, C…) com recomendação de método de campo. | Must |
| US-08 | Como utilizador, exporto o relatório em PDF e os mapas em GeoTIFF/GeoJSON. | Must |
| US-09 | Como geofísico, vejo cada camada e o peso que teve na classificação. | Should |
| US-10 | Como geofísico, ajusto pesos e limiares e reexecuto. | Could |
| US-11 | Como utilizador, vejo avisos claros sobre limitações e incerteza. | Must |
| US-12 | Como utilizador, vejo o terreno e as zonas em 3D para perceber a sua posição no relevo. | Should |
| US-13 | Como utilizador, pergunto em linguagem natural sobre os resultados (ex.: "porque é que a zona A está em primeiro?") e recebo uma resposta simples. | Should |
| US-14 | Como utilizador, filtro as zonas por pedido em linguagem natural (ex.: "só zonas de ferro com mais de 10 ha"). | Should |

## 2. Requisitos funcionais

### Entrada
- **RF-01** O sistema aceita um polígono desenhado no mapa (Leaflet Draw).
- **RF-02** Aceita coordenadas (lat/lon WGS84) e ficheiros GeoJSON e KML.
- **RF-03** Valida que a geometria está em Angola, é válida (sem auto-intersecção) e respeita a área máxima.
- **RF-04** Área máxima inicial: **2 500 km²** [A CALIBRAR]. Acima disso, recusa com mensagem clara.
- **RF-05** Escolha dos alvos: ferro, cobre, ouro, água (um ou vários).

### Aquisição
- **RF-06** Obtém composto Sentinel-2 L2A sem nuvens para a área, em época seca (Maio–Setembro) [A CALIBRAR].
- **RF-07** Obtém Landsat 8/9 Collection 2 L2 como alternativa/validação cruzada.
- **RF-08** Obtém SRTM 1 arc-sec (~30 m) para a área.
- **RF-09** Obtém mapa geológico público para a área, ou usa a cópia local em cache.
- **RF-10** Faz cache local por AOI e versão de dados para evitar descargas repetidas.

### Processamento
- **RF-11** Calcula índices: óxido de ferro, ferroso, alteração argilosa/hidroxilos, NDVI.
- **RF-12** Mascara nuvens, sombras, água e vegetação densa.
- **RF-13** Deriva do SRTM: elevação, declive, hillshade multi-azimute, lineamentos, rede de drenagem, bacias, TWI.
- **RF-14** Reclassifica a litologia em favorável / neutra / desfavorável por alvo, via tabela de regras.
- **RF-15** Normaliza cada camada para 0–1 e calcula a pontuação ponderada por alvo.
- **RF-16** Classifica a pontuação em Alta/Média/Baixa com limiares configuráveis.
- **RF-17** Agrupa pixéis de classe Alta em zonas (A, B, C…), com área, pontuação média e ranking.

### Saída
- **RF-18** Mostra no mapa interactivo: óxido de ferro, argila, elevação, falhas/lineamentos, bacias, probabilidade por alvo.
- **RF-19** Mostra o resumo: classe por alvo, área por classe, lista de zonas.
- **RF-20** Gera recomendação textual por zona (ex.: "magnetometria + resistividade").
- **RF-21** Exporta PDF com mapas, tabelas, metodologia, limitações e data/versão dos dados.
- **RF-22** Exporta GeoTIFF (probabilidade) e GeoJSON (zonas).
- **RF-23** Todo relatório inclui o aviso de que se trata de triagem.
- **RF-25** Assistente de chat no canto da interface que responde a perguntas sobre os resultados da análise actual. Lê só dados estruturados do resultado (zonas, contribuições, qualidade, avisos) através de funções fixas; não calcula nem inventa valores. (Should)
- **RF-26** O assistente converte pedidos de filtro em linguagem natural num filtro estruturado validado; o código executa o filtro e a interface mostra as zonas resultantes. (Should)
- **RF-27** O assistente gera o texto simples do relatório (resumo executivo e recomendações) a partir dos números do resultado. (Should)
- **RF-28** Cada resposta cita os valores usados (zona, área, pontuação, camada) e repete o aviso de triagem quando fala de probabilidade ou recomendações. O assistente recusa afirmar presença certa de minério ou água. (Must, se o assistente existir)
- **RF-29** O assistente é **opcional e nunca bloqueia o sistema**. Usa o Cloudflare Workers AI com o token do próprio utilizador (conta gratuita). Sem token, sem internet ou com a quota esgotada, o painel de chat mostra "Assistente indisponível" e todo o resto funciona igual; o texto do relatório cai para modelos fixos. O utilizador é avisado de que os dados do terreno são enviados à Cloudflare. (Must)
- **RF-30** Qualquer falha do assistente (timeout, erro 403/429, resposta inválida) é capturada e nunca interrompe uma análise nem a exportação. Nenhum fluxo principal depende do assistente. (Must)
- **RF-24** Vista 3D opcional: relevo do SRTM com a camada seleccionada (índice ou probabilidade) e as zonas sobrepostas, com exagero vertical ajustável. A vista 2D é a principal; a 3D nunca é necessária para concluir uma análise. (Prioridade Should)

## 3. Requisitos não funcionais

| ID | Requisito | Meta |
|---|---|---|
| RNF-01 | Desempenho | 10 km² em ≤ 5 min; 2 500 km² em ≤ 20 min (com cache vazio) |
| RNF-02 | Custo | Só serviços gratuitos |
| RNF-03 | Reprodutibilidade | Mesma AOI + mesma versão de dados = mesmo resultado (guardar parâmetros e versões) |
| RNF-04 | Explicabilidade | Contribuição de cada camada visível por zona |
| RNF-05 | Portabilidade | Corre em Windows/Linux; notebook equivalente no Colab |
| RNF-06 | Largura de banda | Interface usável com ligação lenta (mapas leves, resultados em cache) |
| RNF-07 | Privacidade | Terrenos do utilizador não são partilhados nem usados para treino sem consentimento |
| RNF-08 | Robustez | Falha de uma fonte não derruba a análise; resultado marca a camada como indisponível |
| RNF-09 | Testabilidade | Núcleo de análise separado da UI e testável com dados de amostra |
| RNF-10 | Idioma | Interface e relatório em português |

## 4. Critérios de aceitação do MVP

1. Um polígono de 10 km² na Huíla produz os 4 mapas e a classificação final em ≤ 5 min.
2. O relatório PDF abre sem erros e inclui metodologia, versões dos dados e limitações.
3. A mesma execução repetida dá resultado idêntico.
4. Polígonos fora de Angola, inválidos ou grandes demais são recusados com mensagem útil.
5. Pelo menos uma área de teste conhecida (ex.: Longonjo) foi processada e revista por um geofísico.
6. Quando uma fonte falha, o sistema avisa e continua com as restantes camadas.
