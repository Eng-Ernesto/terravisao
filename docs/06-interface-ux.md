# 06 — Interface (UX)

Streamlit, em português. Prioridade: um utilizador não técnico consegue fazer uma análise completa sem ajuda.

## 1. Fluxo principal

```
1. Terreno  →  2. Alvos  →  3. Análise  →  4. Resultados  →  5. Exportar
```

## 2. Ecrãs

### 2.1 Início
- Título, uma frase sobre o que faz.
- Aviso curto: "Ferramenta de triagem. Não substitui o trabalho de campo."
- Botão "Nova análise" e acesso a "Exemplos" (Huíla, Longonjo).

### 2.2 Terreno
- Mapa centrado em Angola; ferramenta de desenhar polígono; edição de vértices.
- Alternativas: colar coordenadas, carregar GeoJSON/KML.
- Mostra em tempo real: área (km²), estado de validação (dentro de Angola, geometria válida, abaixo do limite).
- Mensagens de erro claras (ex.: "O terreno tem 3 800 km². O máximo é 2 500 km².").

### 2.3 Alvos
- Caixas: Ferro, Cobre, Ouro, Água subterrânea.
- Opções avançadas (recolhidas): janela temporal, % máx. de nuvens, pesos (para geofísicos).

### 2.4 Análise
- Barra de progresso por etapa (dados → índices → terreno → pontuação → relatório).
- Estimativa de tempo. Botão cancelar.
- Se uma fonte falhar: aviso amarelo e continua.

### 2.5 Resultados

Layout em duas colunas:

- **Esquerda:** mapa com selector de camada.
- **Direita:** resumo e zonas.

Camadas do mapa:
1. Óxido de ferro
2. Alteração argilosa
3. Elevação (com hillshade)
4. Falhas/lineamentos
5. Bacias e drenagem
6. Geologia
7. Probabilidade por alvo (Baixa/Média/Alta)

Controlos: opacidade, legenda, comparar com imagem de satélite/OSM.

#### Vista 3D (opcional)

- Alternador **2D / 3D** por cima do mapa. O 2D é o padrão e o único usado em desenho do terreno.
- 3D mostra o relevo SRTM da AOI, com a camada activa (índice ou probabilidade) como textura e os contornos das zonas A, B, C… por cima.
- Controlos: exagero vertical (1× a 5×), inclinação/rotação, opacidade da camada.
- Clicar numa zona mostra o mesmo painel de contribuições do 2D.
- Só carrega quando o utilizador a pede; se falhar ou o navegador não suportar WebGL, mantém o 2D e avisa.
- Limite de resolução do relevo na vista 3D (por exemplo, reamostrar a ~60–90 m em AOIs grandes) para manter fluidez [A CALIBRAR].
- O relatório PDF continua a usar mapas 2D; pode incluir uma imagem da vista 3D como extra (fase posterior).

Resumo:
- Cartões por alvo: **classe final** + **confiança**.
- Tabela de zonas: nome, área, pontuação, recomendação.
- Clicar numa zona faz zoom e mostra a contribuição de cada camada (barra horizontal).
- Bloco "Limitações" sempre visível.

### 2.6 Exportar
- PDF do relatório.
- GeoTIFF de probabilidade, GeoJSON de zonas.
- JSON com parâmetros e versões (reprodutibilidade).

## 2.7 Assistente de chat (opcional)

- Painel de chat fixo no canto/lado, recolhível, disponível só depois de existir um resultado.
- Sugestões de perguntas ao abrir: "Resume o resultado", "Porque é que a zona A está em primeiro?", "Que método uso no campo?", "Mostra só zonas com mais de 10 ha".
- Pedidos de filtro actualizam o mapa e a tabela de zonas; o chat mostra o filtro aplicado e pode ser desfeito.
- Cada resposta indica de onde vêm os números (zona, camada) e leva a nota de triagem quando fala de probabilidade.
- Indicador do modo: "Assistente offline (respostas padrão)" ou "Assistente com IA (dados enviados a <fornecedor>)". Consentimento explícito antes do primeiro envio.
- Botão "Gerar texto do relatório" que alimenta o PDF (RF-27).

## 3. Cores e legenda

- Classes: **Baixa** verde-claro/cinza, **Média** amarelo, **Alta** vermelho/laranja. Usar paleta acessível a daltonismo; não depender só da cor (texto e padrões na legenda).
- Mapas contínuos (índices): rampa sequencial de uma só cor.
- Legendas sempre com unidades/ordem de grandeza e nota "relativo à área analisada".

## 4. Relatório PDF

Estrutura:
1. Capa: nome do terreno, data, coordenadas, área.
2. Resumo executivo: classe por alvo, zonas prioritárias, recomendação em 3–5 linhas.
3. Mapas (óxido de ferro, argila, elevação/falhas/bacias, probabilidade).
4. Tabela de zonas.
5. Metodologia resumida (dados, índices, pesos).
6. Qualidade e confiança dos dados.
7. Limitações e avisos.
8. Anexo: versões, IDs das cenas, parâmetros.

Linguagem: simples, sem jargão desnecessário; termos técnicos explicados em glossário.

## 5. Textos obrigatórios

- Aviso no resultado e no PDF: "Este resultado indica probabilidade com base em dados públicos de detecção remota. Não confirma a existência de minerais nem de água no subsolo. Confirme sempre no campo."
- Atribuição de dados (Copernicus, USGS, OneGeology).

## 6. Estados e erros

| Situação | Comportamento |
|---|---|
| Polígono inválido | Bloqueia o botão "Analisar", explica |
| Fora de Angola | Recusa |
| Sem imagem sem nuvens | Alarga janela temporal, avisa; se continuar sem dados, recusa |
| Sem geologia | Continua sem ela, confiança reduzida, aviso |
| Timeout de download | Tenta novamente; senão marca camada indisponível |
| Memória/área excessiva | Recusa antes de começar |

## 7. Acessibilidade e desempenho

- Textos legíveis em ecrãs pequenos; funciona em tablet.
- Mapas renderizados em tiles/PNG leves, não GeoJSON gigantes.
- Resultados guardados em sessão e cache para não recalcular ao mudar de camada.
