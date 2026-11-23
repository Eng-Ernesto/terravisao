# 12 — Direcção visual e design da interface

Referências estudadas: **Felt** (papel quente, serifa, tinta preta, quase sem cor decorativa), **Global Nature Watch** (mapa a ocupar o ecrã, painel lateral de legenda e análise). O protótipo anterior (GeoExplora IA) serve de contra-exemplo: cartões de métricas, emojis, menu de "módulos" e nenhum mapa.

## 1. Princípios

1. **O mapa é o produto.** Ocupa a maior parte do ecrã. Tudo o resto é um painel estreito ao lado.
2. **Sem "cara de IA":** sem gradientes roxos/azuis, sem emojis, sem cartões de métricas vazias, sem brilhos, sem ícones decorativos. Estética de cartografia geológica e de caderno de campo.
3. **Dados primeiro:** cada elemento mostra um dado real (valor, unidade, origem). Nada de texto de marketing no ecrã de trabalho.
4. **Calma e densidade:** muito espaço em branco à volta dos blocos, mas texto compacto dentro deles. Tipografia faz a hierarquia, não caixas coloridas.
5. **Honestidade visual:** probabilidade sempre ao lado da confiança; o aviso de triagem tem lugar fixo e discreto.

## 2. Paleta (inspirada em materiais geológicos)

| Papel | Cor | Uso |
|---|---|---|
| Papel | `#F4F1EA` | Fundo geral |
| Papel escuro | `#EAE5D9` | Painéis, separadores |
| Tinta | `#1C1B18` | Texto e título |
| Tinta suave | `#6B675D` | Texto secundário, legendas |
| Linha | `#D8D2C4` | Bordas finas (1 px) |
| Óxido (acento) | `#B4532A` | Ação principal, classe Alta, zonas |
| Ocre | `#C9A227` | Classe Média |
| Musgo | `#5E7A63` | Classe Baixa |
| Basalto | `#2B2F33` | Barra superior, modo escuro do mapa |

Regras: um único acento (óxido). Classes Baixa/Média/Alta usam musgo/ocre/óxido e **também** rótulo de texto (acessível a daltonismo). Contraste mínimo 4.5:1 para texto.

## 3. Tipografia

- **Títulos e nome do produto:** serifa (Fraunces ou Source Serif 4). Pesos 500–600.
- **Interface:** sans neutra (Inter ou IBM Plex Sans), 14 px base.
- **Números, coordenadas, unidades:** IBM Plex Mono (alinha casas decimais).
- Fontes empacotadas em `app/static/fonts/` (o Docker funciona offline); alternativa: Georgia / system-ui.

## 4. Layout

```
┌────────────────────────────────────────────────────────────────┐
│ TerraVisão  ·  Longonjo, Huambo            13°S 15°E   [Exportar]│  barra fina
├──────────────┬─────────────────────────────────────────────────┤
│ Alvo         │                                                 │
│ ◉ Ferro      │                                                 │
│ ○ Cobre      │                  MAPA                           │
│ ○ Ouro       │            (ecrã quase inteiro)                 │
│ ○ Água       │                                                 │
│              │                                                 │
│ Camadas      │                                                 │
│ ☑ Zonas      │          ┌────────────────────┐                 │
│ ☑ Pontuação  │          │ legenda            │                 │
│ ☐ Óxido ferro│          └────────────────────┘                 │
│ ...          │                                                 │
├──────────────┴─────────────────────────────────────────────────┤
│ Resultado: FERRO  Média · confiança média     Zonas A  B  C ...│  faixa inferior
└────────────────────────────────────────────────────────────────┘
```

- **Painel esquerdo (~280 px):** alvo, camadas, opacidade. Sem menu de módulos.
- **Faixa inferior ou painel direito recolhível:** classe final, confiança, tabela de zonas, aviso de triagem.
- **Barra superior fina:** nome do terreno, coordenadas, exportar.
- Assistente de chat (opcional): gaveta que abre à direita, fechada por defeito.

## 5. Componentes

- **Chip de classe:** texto + ponto de cor (ex.: ● Média). Sem fundo saturado.
- **Zona:** linha de tabela com letra (A, B…), área em ha, pontuação, método de campo.
- **Barra de contribuição:** barras horizontais finas em tinta, por camada.
- **Legenda do mapa:** rampa discreta, unidade e nota "relativo à área analisada".
- **Aviso de triagem:** uma linha em tinta suave, sempre visível; nunca em caixa de alerta.

## 6. Mapa

- Base clara e calma (CartoDB Positron) por defeito; satélite (Esri World Imagery) como alternativa.
- Camadas raster em PNG transparente com rampas sequenciais de uma só cor; zonas como contornos de óxido, sem preenchimento forte.
- Contorno da área analisada em tinta fina e tracejada.

## 7. O que a tecnologia permite

Streamlit permite estilo por CSS (paleta, tipografia, painéis) e mapa de largura total, mas não permite painéis flutuantes sobre o mapa nem animações finas. A direcção acima foi desenhada para caber nesses limites: painel lateral fixo e faixa de resultado, não cartões sobrepostos. Se mais tarde for preciso um nível de acabamento superior, a evolução é um frontend próprio (MapLibre) a falar com o mesmo pacote `terravisao`, como previsto na fase 2 (ADR-11).

## 8. Fora do ecrã de trabalho

Ecrã inicial mínimo: nome em serifa, uma frase, botão "Abrir exemplo (Longonjo)" e "Nova análise". Sem lista de módulos.
