# 14 — GeoExplora IA: visão, módulos e âmbito

> Apresentação: 3.ª SAGEO, 25 a 27 de Novembro. Roteiro em [15-roteiro-demonstracao.md](15-roteiro-demonstracao.md).

> Documento vivo. Regista o que a equipa do projecto pediu, o que entra na versão de demonstração e **porque é que cada ideia entrou ou ficou de fora**.

## 1. Produto

**GeoExplora IA** é a plataforma. Ajuda o geofísico a interpretar dados de exploração de **terras raras e minerais críticos para a transição energética limpa em Angola**.

Duas formas de usar, na mesma interface:

| Módulo | O que faz | Quem fornece os dados |
|---|---|---|
| **Análise de mapa** (principal) | O geofísico carrega os seus dados (amostras geoquímicas, mapas e grelhas geofísicas). A plataforma analisa, classifica anomalias, delimita zonas de interesse, relaciona geoquímica com geofísica e explica o resultado num **assistente de chat** e num relatório. | O geofísico (CSV, GeoTIFF, GeoJSON, Shapefile) |
| **TerraVisão** (módulo de detecção remota) | O utilizador desenha o terreno e a plataforma obtém imagens de satélite e relevo públicos, calcula índices e zonas de triagem. Pode servir de contexto (imagem de satélite, relevo) à análise de mapa. | Dados públicos (Sentinel-2, Copernicus DEM) |

Nome: o produto chama-se **GeoExplora IA** (é o nome da equipa). **TerraVisão** é o nome do módulo.

## 2. Alvo

**Minerais críticos para a transição energética e industrial de Angola.** É o tema da 3.ª Semana Académica de Geociências (SAGEO, 25 a 27 de Novembro): «Do petróleo aos minerais críticos: o papel dos georecursos na transição energética e industrial de Angola».

O caso de demonstração são as **terras raras de Longonjo (Huambo)**, um carbonatito, com ênfase nos elementos para ímanes permanentes (Nd, Pr) usados em turbinas eólicas e motores eléctricos. O motor aceita também outros elementos críticos (por exemplo cobre ou lítio): se os dados não tiverem terras raras, analisa o elemento escolhido. No módulo TerraVisão, o cobre (electrificação) e o ferro entram como minerais de interesse.

## 3. Dados da demonstração

Fictícios, fornecidos pela equipa (500 amostras com Ce, La, Nd, Pr em ppm e uma anomalia magnética de teste). Dois conjuntos:

1. **Dados da equipa (Longonjo):** exactamente os ficheiros recebidos. As coordenadas originais caem a cerca de 7,2° S, fora de Longonjo; o deslocamento rígido (+22 536 m em X, −631 169 m em Y) usado pela própria equipa é aplicado e indicado. Os valores são aleatórios sem relação espacial, por isso o resultado correcto é «não há relação detectável».
2. **Modelo sintético coerente (Longonjo):** gerado por nós, com um corpo carbonatítico fictício onde o enriquecimento em terras raras coincide com um alto magnético. Serve para mostrar o que a plataforma faz quando há relação nos dados. **Está sempre rotulado como fictício.**

## 4. Registo de âmbito: o que entra e o que fica de fora

Legenda: ✅ entra hoje · 🟡 parcial · ⏳ fase seguinte · ❌ fora do âmbito actual

| # | Ideia da equipa | Estado | Justificação |
|---|---|---|---|
| 1a | Carregar mapas e dados próprios (CSV, GeoTIFF, GeoJSON, Shapefile) | ✅ | Núcleo da proposta; ferramentas maduras (rasterio, geopandas) |
| 1b | Grelhas magnéticas e derivadas (1.ª derivada vertical, sinal analítico, gradiente horizontal) | ✅ | Cálculo por FFT sobre a grelha carregada; testável com anomalia sintética |
| 1c | RTP (redução ao pólo) | ⏳ | Precisa de inclinação e declinação do campo e de validação pelo geofísico; um RTP mal feito engana |
| 1d | Gravimetria | 🟡 | Entra como grelha genérica (visualização, derivadas, amostragem nos pontos); sem processamento próprio (Bouguer, etc.) |
| 1e | Descarregar dados geofísicos públicos automaticamente | ❌ | Os modelos globais têm resolução de vários km e os levantamentos de Angola dependem de acesso a confirmar |
| 2 | Geologia de maior resolução | 🟡 | Carregamento e visualização de camadas geológicas entra; a escala de dados oficiais (que não temos) é o limite |
| 3a | IA: classificação de anomalias e zonas favoráveis | ✅ | Regras estatísticas (quantis, robustas) e agrupamento espacial: leves e explicáveis |
| 3b | IA: modelo supervisionado com explicação | ✅ (com ressalva) | Random Forest com validação espacial e importância das variáveis. Diz honestamente quando **não supera o acaso** (é o caso dos dados da equipa) |
| 3c | IA: assistente de chat que analisa o mapa | ✅ | Cloudflare Workers AI com o token do utilizador; modo offline de reserva. Lê só os resultados calculados |
| 3d | Reconhecimento de padrões por redes neuronais | ❌ | Exige dados reais rotulados e hardware que os computadores disponíveis não têm |
| 4 | Importação a partir do QGIS | ✅ | Coberto por 1a |
| 5 | Sobreposição de camadas (visibilidade, transparência, simbologia) | ✅ | Controlo de camadas e opacidade; a simbologia fica limitada ao que o Streamlit permite |
| 6 | Validação científica | ⏳ | Depende de dados reais e do geofísico; a plataforma mostra métricas e limites, mas a validação é trabalho de campo |
| 7 | Relatórios técnicos | ✅ | PDF com mapas, dados, metodologia, parâmetros, resultados, limitações e (se disponível) interpretação da IA |
| 8 | Terras raras: TREO, razão NdPr/TREO | ✅ | Cálculo directo e relevante para o tema (ímanes permanentes) |
| 9 | TerraVisão como módulo | ✅ | Reaproveita o trabalho já feito |
| 10 | Vista 3D | ⏳ | Fora do tempo de hoje; não bloqueia a demonstração |
| 11 | Testes em várias regiões de Angola | ⏳ | Precisa de dados reais |
| 12 | Contas de utilizador e partilha | ❌ | Não é necessário para a demonstração presencial |

## 4.1 Estado de implementação (24 de Novembro)

| Parte | Estado |
|---|---|
| Carregar CSV, GeoJSON, Shapefile (zip) e GeoTIFF | Feito e testado |
| Terras raras: TREO (parcial ou total) e NdPr/TREO; outro elemento crítico se não houver terras raras | Feito e testado |
| Classes de anomalia, superfície, zonas com teste de permutação | Feito e testado |
| Derivadas magnéticas (1.ª vertical, gradiente horizontal, sinal analítico) | Feito e testado |
| Relação com a geofísica e modelo com validação por blocos espaciais | Feito e testado |
| Assistente offline (respostas e interpretação automática) | Feito e testado |
| Assistente com Cloudflare Workers AI | Testado de ponta a ponta **contra o serviço real** através da CLI `cf` (conta do utilizador): prompt, contexto, escolha de modelo, recurso a outro modelo e recusa de certezas. **Por exercitar:** o pedido HTTP directo com token (a documentação foi seguida, mas não foi chamado) |
| Relatório técnico em PDF | Feito |
| Interface com os dois módulos | Feita e verificada no navegador |
| Docker | Actualizado; **continua por testar** numa máquina com Docker |

## 5. Como a IA se divide (o que é leve e o que não é)

| Componente | Onde corre | Peso | Precisa de internet |
|---|---|---|---|
| Classificação, agrupamento de zonas, interpolação, derivadas | Local (numpy/scipy/scikit-learn) | Leve (segundos) | Não |
| Random Forest, importâncias, validação cruzada espacial | Local (scikit-learn) | Leve (500 amostras: poucos segundos) | Não |
| Assistente de chat com linguagem livre | Cloudflare Workers AI (conta do utilizador) | Nada na máquina local | Sim, e token |
| Assistente offline (respostas padrão e interpretação automática) | Local | Nenhum | Não |

Regra: **o assistente nunca calcula nem inventa**. Lê um resumo estruturado dos resultados. Sem internet ou token, a plataforma funciona na mesma e o chat responde com o modo offline.

### 5.1 Modelo do assistente (teste real, 24 de Novembro)

Testados com o pedido real do assistente (resumo da análise + pergunta), na conta do utilizador:

| Modelo | Neurons / pergunta | Tempo | Resultado |
|---|---|---|---|
| `@cf/mistralai/mistral-small-3.1-24b-instruct` | ~42 | 3 s | **Escolhido.** Cita os números, recusa garantir minério e diz que os dados são fictícios |
| `@cf/meta/llama-4-scout-17b-16e-instruct` | ~33 | 5 s | Bom; primeira alternativa |
| `@cf/openai/gpt-oss-20b` | ~27 | 5 s | Bom, com um erro de redacção; segunda alternativa |
| `@cf/ibm-granite/granite-4.0-h-micro` | ~3,5 | 8 s | Barato, mas mais solto |
| `@cf/meta/llama-3.1-8b-instruct` | ~6 | 1,5 s | Responde, mas **fora da lista do catálogo**: pode ser retirado |
| `@cf/google/gemma-4-26b-a4b-it`, `@cf/zai-org/glm-4.7-flash` | ~24 | 9 a 13 s | **Inutilizáveis**: modelos de raciocínio gastam os tokens a pensar e devolvem resposta vazia |

Com ~42 neurons por pergunta, a quota gratuita de 10 000 neurons por dia dá para cerca de 230 perguntas (o plano da conta usada nos testes não foi verificado). O código recorre ao modelo seguinte se um estiver indisponível ou devolver vazio, e garante sempre o aviso de «dados fictícios» nas respostas da IA.

## 6. Arquitectura

```
GeoExplora IA  (interface Streamlit, módulos)
├── Análise de mapa      ──► pacote geoexplora  (dados, terras raras, análise, geofísica, IA, relatório)
└── TerraVisão (satélite) ──► pacote terravisao  (satélite, terreno, pontuação, zonas, relatório)
```

Os dois pacotes partilham a fronteira de Angola, a grelha UTM e o estilo de relatório. A análise de mapa pode usar como contexto os resultados do TerraVisão (imagem de satélite e relevo da mesma área).
