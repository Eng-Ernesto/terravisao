# 15 — Roteiro de demonstração (SAGEO, 25 a 27 de Novembro)

Tema do evento: *Do petróleo aos minerais críticos: o papel dos georecursos na transição energética e industrial de Angola.*

## Mensagem

> O GeoExplora IA ajuda o geofísico a **interpretar os seus dados** de minerais críticos mais depressa: classifica anomalias, delimita zonas de interesse, relaciona a geoquímica com a geofísica e explica o resultado. Não substitui o trabalho de campo: indica **onde vale a pena confirmar**.

## Antes de começar (2 minutos)

1. `docker compose up` (ou `streamlit run app/streamlit_app.py`) e abrir http://localhost:8501.
2. Com ou sem internet, tudo funciona. O Assistente com IA em linguagem livre precisa de internet e de token (opcional); sem eles responde offline.
3. Confirmar que aparece a etiqueta **«Dados fictícios · demonstração»**.

## Sequência (6 a 7 minutos)

| Minuto | O que mostrar | O que dizer |
|---|---|---|
| 0:00 | Ecrã inicial: Análise de mapa, dados da equipa | «500 amostras de terras raras de Longonjo (dados fictícios da equipa) sobre imagem de satélite.» |
| 1:00 | Pontos por classe; ligar «Superfície» | «Classes de anomalia: baixa, moderada e elevada. A superfície mostra onde o teor sobe.» |
| 2:00 | Assistente: «Resume o resultado» e «O modelo funciona?» | «Neste conjunto não há estrutura: o modelo não supera o acaso e nenhuma zona é maior do que o acaso. A plataforma diz isto de forma honesta.» |
| 3:30 | Trocar para «modelo sintético coerente» | «Agora um modelo fictício com um corpo carbonatítico: terras raras, tório e um alto magnético coincidem.» |
| 4:00 | Zona A; correlação com tório e magnética; «Grelha geofísica» → sinal analítico | «A zona A aparece sobre o corpo. O sinal analítico delimita a fonte magnética. O modelo supera o acaso.» |
| 5:00 | NdPr/TREO na tabela; pergunta «Qual a fracção de NdPr?» | «NdPr é a parte para ímanes permanentes de turbinas e motores eléctricos: a ligação à transição energética.» |
| 5:30 | Descarregar o relatório técnico (PDF) | «Mapas, estatística, zonas, metodologia e limitações num relatório.» |
| 6:00 | Módulo TerraVisão (satélite) | «Quando não há dados próprios, o TerraVisão faz a triagem por satélite público de qualquer terreno.» |

## Perguntas prováveis e respostas honestas

**Os dados são reais?** Não. São fictícios (os da equipa são aleatórios; o modelo coerente foi gerado para demonstração). A plataforma está pronta para dados reais.

**A IA prevê onde há minério?** Não. Classifica e relaciona os dados que o geofísico traz e diz quando a relação não existe. Só indica onde confirmar.

**Qual o papel do Random Forest?** Testa se a geofísica (magnetometria, tório) prevê a geoquímica, com validação por blocos espaciais. Se não superar o acaso, avisa.

**O que são «zonas maiores que o acaso»?** Zonas com mais amostras elevadas do que 95 % das redistribuições aleatórias das mesmas amostras (teste de permutação).

**E o RTP, a gravimetria e a geologia detalhada?** Estão previstos: o RTP precisa de validação do geofísico; a gravimetria entra como grelha; a geologia depende de obter os dados oficiais.

**Funciona offline?** Sim, tudo menos o Assistente com IA em linguagem livre e a análise nova de satélite (TerraVisão).

**A IA que responde no chat é local?** O modo offline é local. A IA em linguagem livre usa o Cloudflare Workers AI com a conta de quem usa, e só vê o resumo dos resultados.

## O que não prometer

- Que os resultados representam mineralização real.
- Que o modelo funciona sempre: com os dados da equipa não funciona, e isso é o correcto.
- Que o Docker já foi testado noutra máquina.
- Que a IA em linguagem livre já foi testada contra a API real: só foi testada com respostas simuladas.
